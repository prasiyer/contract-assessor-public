import os
from datetime import datetime
import base64
import pandas as pd
import fitz
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable

from config import (
    CONTRACT_QUESTION_FILE_PATH,
    CONTRACT_TEXT_WIP_FILE_PATH,
    DEFAULT_ASSESSOR_MODEL_ID,
    DOC_TO_IMAGE_CONVERTER,
    TEST_CONTRACT_FILE_PATH,
    TOKEN_USAGE_FILE_PATH,
    LOGGER,
)
from services.oai_client import oai_client

from static_assets import (
    contract_evaluation_prompts,
    prompts_doc_processing,
    scoring_rubric,
)

quant_scoring_rubric = scoring_rubric.quant_scoring_rubric_v1
qual_scoring_rubric = scoring_rubric.qual_scoring_rubric


class ContractAssessor:
    """Contract assessment system that extracts, scores, and evaluates contract parameters.
    
    This class handles the complete workflow of contract assessment:
    1. Convert PDF contract to text using vision LLM
    2. Extract contract parameters based on predefined questions
    3. Score extracted parameters against rubrics
    4. Generate assessment report for low-scoring parameters
    
    Supports two test modes:
    - test_mode: Process only first 4 pages of PDF (faster testing)
    - use_test_file: Skip PDF conversion, use pre-converted test file
    
    Note: Token usage tracking depends on oai_client.py. Concurrent instances
    may have CSV write conflicts - known limitation for batch processing.
    
    Attributes:
        model_id: LLM model identifier for processing
        input_contract_path: Path to input PDF contract file
        test_mode: If True, process only first 4 pages
        use_test_file: If True, skip PDF conversion and use test file
        progress_callback: Optional callback for progress updates (message, percent)
    """
    
    # Class constants for configuration
    DEFAULT_QUESTIONS_PER_BATCH = 5
    DEFAULT_CHUNKING_METHOD = "langchain_markdown_splitter"
    TEST_MODE_PAGE_LIMIT = 4
    MAX_TOKENS_EXTRACTION = 5000
    MAX_TOKENS_ASSESSMENT = 3000
    MAX_FILE_SIZE_MB = 50
    
    # Question type constants
    QUESTION_TYPE_QUALITATIVE = "qualitative"
    QUESTION_TYPE_QUANTITATIVE = "quantitative"
    QUESTION_TYPE_OTHER = "other"
    
    # Chunking method constants
    CHUNKING_METHOD_LLM = "llm_chunking"
    CHUNKING_METHOD_LANGCHAIN = "langchain_markdown_splitter"
    
    # Answer constants
    UNIT_NOT_APPLICABLE = "Not applicable"
    ANSWER_NOT_SPECIFIED = "NOT_SPECIFIED"
    def __init__(
        self,
        model_id: str = DEFAULT_ASSESSOR_MODEL_ID,
        input_contract_path: Optional[str] = None,
        test_mode: bool = False,
        use_test_file: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> None:
        """Initialize ContractAssessor with validation and configuration.
        
        Args:
            model_id: LLM model identifier (default from config)
            input_contract_path: Path to PDF contract file to process
            test_mode: If True, process only first 4 pages for faster testing
            use_test_file: If True, skip PDF conversion and use pre-converted test file
            progress_callback: Optional callback function(message: str, percent: float) for progress updates
            
        Raises:
            ValueError: If model_id is empty, file size exceeds limit, or invalid file type
            FileNotFoundError: If input_contract_path doesn't exist
            PermissionError: If output directory is not writable
        """
        # Validate model_id
        if not model_id or not model_id.strip():
            raise ValueError("model_id cannot be empty")
        
        # Validate input contract path if provided and not using test file
        if input_contract_path and not use_test_file:
            contract_path = Path(input_contract_path).resolve()
            
            # Check file exists
            if not contract_path.exists():
                raise FileNotFoundError(f"Contract file not found: {input_contract_path}")
            
            # Check file is readable
            if not contract_path.is_file():
                raise ValueError(f"Path is not a file: {input_contract_path}")
            
            # Check file extension
            if contract_path.suffix.lower() != '.pdf':
                raise ValueError(f"Only PDF files are supported. Got: {contract_path.suffix}")
            
            # Check file size
            file_size_mb = contract_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                raise ValueError(
                    f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({self.MAX_FILE_SIZE_MB}MB)"
                )
            
            LOGGER.info(f"Validated contract file: {contract_path.name} ({file_size_mb:.2f}MB)")
        
        # Validate output directory is writable
        output_path = Path(CONTRACT_TEXT_WIP_FILE_PATH)
        if not output_path.parent.exists():
            raise FileNotFoundError(f"Output directory does not exist: {output_path.parent}")
        if not os.access(output_path.parent, os.W_OK):
            raise PermissionError(f"Output directory is not writable: {output_path.parent}")
        
        # Initialize core attributes
        self.model_id = model_id
        self.llm_client = oai_client(model_id=model_id)
        self.progress_callback = progress_callback
        
        # Token usage tracking - load existing data or create new DataFrame
        self.token_usage_file = TOKEN_USAGE_FILE_PATH
        try:
            self.token_usage_df = pd.read_csv(self.token_usage_file)
            LOGGER.debug(f"Loaded token usage file: {self.token_usage_file}")
        except FileNotFoundError:
            LOGGER.warning(f"Token usage file not found, creating new: {self.token_usage_file}")
            self.token_usage_df = pd.DataFrame(columns=[
                'timestamp', 'doc_name', 'doc_type', 'operation', 'page_number',
                'prompt_tokens', 'completion_tokens', 'total_tokens', 'model_id'
            ])
        except Exception as e:
            LOGGER.error(f"Error loading token usage file: {e}")
            raise
        
        # Initialize prompt templates
        self.pdf_to_text_message = self.create_pdf_to_text_message()
        self.parameter_extraction_message = self.create_parameter_extraction_message()
        
        # Contract processing configuration
        self.input_contract_path = input_contract_path
        self.contract_text_path = CONTRACT_TEXT_WIP_FILE_PATH  # Output file for extracted text
        self.doc_type = "contract"
        self.doc_to_image_converter = DOC_TO_IMAGE_CONVERTER
        self.num_pages_to_process = -1  # -1 means process all pages
        self.chunking_method = self.DEFAULT_CHUNKING_METHOD
        self.questions_per_batch = self.DEFAULT_QUESTIONS_PER_BATCH
        
        # Test mode configuration
        self.test_mode = test_mode
        self.use_test_file = use_test_file
        
        # Load contract questions - using latin1 encoding for backward compatibility
        # TODO: Migrate to UTF-8 encoding in future version
        try:
            contract_questions_df = pd.read_csv(
                CONTRACT_QUESTION_FILE_PATH, 
                encoding='latin1'
            )
            contract_questions_df = contract_questions_df[contract_questions_df["Status"] != "remove"]
            self.contract_questions_df = contract_questions_df
            LOGGER.info(f"Loaded {len(contract_questions_df)} contract questions")
        except Exception as e:
            LOGGER.error(f"Error loading contract questions: {e}")
            raise
        
        # Apply test mode settings
        if test_mode:
            self.num_pages_to_process = self.TEST_MODE_PAGE_LIMIT
            LOGGER.info(f"Test mode enabled: processing only {self.TEST_MODE_PAGE_LIMIT} pages")
        



    def create_pdf_to_text_message(self) -> List[Dict[str, Any]]:
        """Create message template for PDF to text conversion.
        
        Returns:
            List of message dictionaries for LLM API call
        """
        pdf_conv_system_prompt = prompts_doc_processing.system_prompt_doc_extraction_v9_2
        input_uri = ""
        pdf_to_text_message = [
            {"role": "system", "content": pdf_conv_system_prompt},
            {"role": "user", "content": [{
                    "type": "image_url",
                    "image_url": {"url": f"{input_uri}"}
                    }]
                },
        ]
        return pdf_to_text_message
    
    def create_parameter_extraction_message(self) -> List[Dict[str, Any]]:
        """Create message template for parameter extraction from contract.
        
        Returns:
            List of message dictionaries for LLM API call
        """      
        input_contract_str = ""
        contract_questions = ""

        parameter_extraction_message = [
            {"role": "system", "content": ""},
            {"role": "user", "content": [{
                    "type": "text",
                    "text": f"## CONTRACT: \n{input_contract_str} ## QUESTIONS: \n {contract_questions}"
                    }]
                },
        ]
        return parameter_extraction_message

    def contract_assessment_message(self, input_low_score_rows_str: str) -> List[Dict[str, Any]]:
        """Create message template for contract assessment.
        
        Args:
            input_low_score_rows_str: JSON string of low-scoring parameters
            
        Returns:
            List of message dictionaries for LLM API call
        """
        contract_assessment_system_prompt = contract_evaluation_prompts.contract_assessment_prompt
        contract_assessment_message = [
            {"role": "system", "content": contract_assessment_system_prompt},
            {"role": "user", "content": [{
                    "type": "text",
                    "text": f"## CONTRACT: \n{input_low_score_rows_str}"
                    }]
                },
        ]
        return contract_assessment_message

    # def pdf_to_images_fitz(input_doc_path, num_pages=-1):
    def pdf_to_images_fitz(self, num_pages: int = -1) -> List[bytes]:
        """Convert PDF document to a list of PNG images.

        Args:
            num_pages: Number of pages to convert. If -1, converts all pages.

        Returns:
            List of PNG images as bytes
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If PDF is corrupted or cannot be opened
            ValueError: If num_pages is invalid (not -1 or positive)
        """
        if num_pages != -1 and num_pages < 1:
            raise ValueError(f"num_pages must be -1 or positive integer, got: {num_pages}")
        
        doc = None
        try:
            doc = fitz.open(self.input_contract_path)
            images = []
            total_pages = len(doc)
            pages_to_process = total_pages if num_pages == -1 else min(num_pages, total_pages)
            
            LOGGER.info(f"Converting {pages_to_process} pages of PDF to images")
            
            for page_num in range(pages_to_process):
                try:
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = pix.tobytes("png")
                    images.append(img)
                except Exception as e:
                    LOGGER.error(f"Error processing page {page_num + 1}: {e}")
                    raise RuntimeError(f"Failed to process page {page_num + 1}: {e}") from e
                    
            LOGGER.info(f"Successfully converted {len(images)} pages to images")
            return images
            
        except FileNotFoundError:
            LOGGER.error(f"PDF file not found: {self.input_contract_path}")
            raise
        except RuntimeError as e:
            LOGGER.error(f"Failed to open or process PDF: {e}")
            raise
        except Exception as e:
            LOGGER.error(f"Unexpected error processing PDF: {e}")
            raise RuntimeError(f"Failed to convert PDF to images: {e}") from e
        finally:
            if doc is not None:
                doc.close()
                LOGGER.debug("PDF document closed")

    def fitz_image_to_uri(self, image: bytes) -> str:
        """Convert an image to a base64-encoded data URI.

        Args:
            image: The image in bytes format (PNG)

        Returns:
            Base64-encoded data URI string
        """
        return "data:image/png;base64," + base64.b64encode(image).decode('utf-8') 

    # def extract_info_from_doc_info(processor_llm_client, prompt_message, input_doc, output_file, chunking_method, num_pages = -1):
    def convert_pdf_to_text(self) -> None:
        """Extract text from PDF by converting to images and processing with vision LLM.
        
        Converts each PDF page to an image, sends to LLM for text extraction,
        and writes results to output file in XML/markdown format. Tracks token
        usage for each page. Results stored in self.contract_text_str.
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            IOError: If unable to write to output file
            RuntimeError: If PDF conversion or LLM processing fails
        """
        input_doc_path = self.input_contract_path
        doc_name = os.path.basename(input_doc_path)
        doc_type = self.doc_type
        num_pages = self.num_pages_to_process
        output_file = self.contract_text_path
        chunking_method = self.chunking_method
        prompt_message = self.pdf_to_text_message
        
        LOGGER.info(f"Starting PDF to text extraction for {doc_name}")
        
        try:
            # Convert PDF pages to images
            images = self.pdf_to_images_fitz(num_pages)
            total_images = len(images)
            
            # Update progress
            if self.progress_callback:
                self.progress_callback(f"Converted {total_images} pages to images", 0.1)
            
            consolidated_response = ""
            token_usage_records = []  # Collect records for batch DataFrame creation
            
            # Process each page
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    # Write document opening tag
                    f.write(f'<document doc_name="{doc_name}" doc_type="{doc_type}">\n')
                    
                    LOGGER.info(f"Processing {total_images} pages with vision LLM")
                    
                    for i, image in enumerate(images):
                        page_num = i + 1
                        
                        try:
                            # Convert image to base64 URI
                            image_uri = self.fitz_image_to_uri(image)
                            prompt_message[1]["content"][0]["image_url"]["url"] = image_uri
                            
                            LOGGER.info(f"Processing page {page_num}/{total_images}")
                            
                            # Get LLM response
                            response_str, token_usage, _ = self.llm_client.get_response_with_token_tracking(
                                prompt_message
                            )
                            
                            # Track token usage
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                            token_usage_records.append({
                                'timestamp': current_time,
                                'doc_name': doc_name,
                                'doc_type': doc_type,
                                'operation': 'assessor_extraction',
                                'page_number': page_num,
                                'prompt_tokens': token_usage.prompt_tokens,
                                'completion_tokens': token_usage.completion_tokens,
                                'total_tokens': token_usage.total_tokens,
                                'model_id': self.model_id,
                            })
                            
                            # Format response based on chunking method
                            if chunking_method == self.CHUNKING_METHOD_LLM:
                                response_str = f'<doc_page number="{page_num}">\n' + response_str + "\n</doc_page>"
                            elif chunking_method == self.CHUNKING_METHOD_LANGCHAIN:
                                response_str = f"<!-- page_number={page_num} -->\n" + response_str
                            
                            consolidated_response += response_str + "\n"
                            f.write(response_str + "\n\n")
                            
                            # Update progress
                            progress = 0.1 + (0.3 * page_num / total_images)
                            if self.progress_callback:
                                self.progress_callback(
                                    f"Processed page {page_num}/{total_images}", 
                                    progress
                                )
                                
                        except Exception as e:
                            LOGGER.error(f"Error processing page {page_num}: {e}")
                            raise RuntimeError(f"Failed to process page {page_num} of {doc_name}: {e}") from e
                    
                    # Write document closing tag
                    consolidated_response += "</document>\n"
                    f.write("</document>\n")
                    
            except IOError as e:
                LOGGER.error(f"Error writing to output file {output_file}: {e}")
                raise IOError(f"Failed to write extracted text to {output_file}: {e}") from e
            
            # Store consolidated response
            self.contract_text_str = consolidated_response
            LOGGER.info(f"Successfully extracted text from {total_images} pages")
            
            # Batch update token usage DataFrame (much faster than row-by-row)
            if token_usage_records:
                new_usage_df = pd.DataFrame(token_usage_records)
                self.token_usage_df = pd.concat(
                    [self.token_usage_df, new_usage_df], 
                    ignore_index=True
                )
                self.token_usage_df.to_csv(self.token_usage_file, index=False)
                LOGGER.debug(f"Saved token usage for {len(token_usage_records)} pages")
            
            if self.progress_callback:
                self.progress_callback("PDF text extraction complete", 0.4)
                
        except Exception as e:
            LOGGER.error(f"Failed to convert PDF to text: {e}")
            raise

    def split_question_df_into_batches(self, questions: pd.DataFrame, questions_per_batch: int) -> List[str]:
        """Split questions DataFrame into batches of formatted question strings.
        
        Args:
            questions: DataFrame with 'Question_ID' and 'extraction_question_revised' columns
            questions_per_batch: Number of questions per batch
            
        Returns:
            List of formatted question batch strings
        """
        question_batches = []
        for i in range(0, len(questions), questions_per_batch):
            question_batch = questions[i:i + questions_per_batch]
            question_batch_with_prefix = [
                f"{q['Question_ID']}: {q['extraction_question_revised']}" 
                for q in question_batch.to_dict('records')
            ]
            question_batch_string = "\n\n".join(question_batch_with_prefix) + "\n\n"
            question_batches.append(question_batch_string)
        return question_batches

    def create_question_batches(self, question_type: str) -> List[str]:
        """Create batches of questions filtered by type.
        
        Args:
            question_type: Type of questions ('qualitative', 'quantitative', or 'other')
            
        Returns:
            List of question batch strings ready for LLM processing
        """
        questions_per_batch = self.questions_per_batch
        contract_questions_df = self.contract_questions_df
        
        # Filter questions by type
        if question_type == self.QUESTION_TYPE_OTHER:
            question_list = contract_questions_df[
                ~contract_questions_df['type'].isin(
                    [self.QUESTION_TYPE_QUALITATIVE, self.QUESTION_TYPE_QUANTITATIVE]
                )
            ][["Question_ID", 'extraction_question_revised']]
        else:
            question_list = contract_questions_df[
                contract_questions_df['type'] == question_type
            ][["Question_ID", 'extraction_question_revised']]
        
        question_batches = self.split_question_df_into_batches(question_list, questions_per_batch)
        return question_batches
    # def extract_parameter_from_contract(input_contract_str: str, q_type: str) -> None:

    def extract_clean_json(self, llm_output: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM output, removing code block markers.
        
        Args:
            llm_output: Raw LLM response potentially containing ```json markers
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If JSON is malformed or cannot be parsed
        """
        LOGGER.debug(f"Cleaning JSON output (length: {len(llm_output)})")
        
        # Remove triple backticks and optional 'json' label
        cleaned = llm_output
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        LOGGER.debug(f"Cleaned JSON (length: {len(cleaned)})")
        
        # Parse JSON with error handling
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            LOGGER.error(f"Failed to parse JSON from LLM. Error: {e}")
            LOGGER.error(f"Problematic JSON (first 500 chars): {cleaned[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e
    
    def extract_parameter_from_contract(self) -> None:
        """Extract contract parameters by querying LLM with batched questions.
        
        Processes qualitative, quantitative, and other question types in batches,
        sending contract text and questions to LLM for structured extraction.
        Results stored in self.parameter_from_contract_df.
        
        Raises:
            ValueError: If LLM returns malformed JSON response
            RuntimeError: If contract_text_str not initialized (call convert_pdf_to_text first)
            KeyError: If required fields missing from LLM response
        """
        # Validate contract text is available
        if not hasattr(self, 'contract_text_str') or not self.contract_text_str:
            raise RuntimeError("Contract text not available. Call convert_pdf_to_text() first.")
        
        question_type_list = [
            self.QUESTION_TYPE_QUALITATIVE, 
            self.QUESTION_TYPE_QUANTITATIVE, 
            self.QUESTION_TYPE_OTHER
        ]
        input_contract_str = self.contract_text_str
        batch_parameter_message = self.parameter_extraction_message
        contract_file_name = os.path.basename(self.input_contract_path)
        
        # Prompt templates for different question types
        qual_parameter_prompt = contract_evaluation_prompts.MSA_parameter_qual_extraction_prompt_v8
        quant_parameter_prompt = contract_evaluation_prompts.MSA_parameter_quant_extraction_prompt_v3
        other_parameter_prompt = contract_evaluation_prompts.MSA_parameter_other_extraction_prompt_v3
        
        # Collect parameter records for efficient DataFrame creation
        parameter_records = []
        total_batches = sum(
            len(self.create_question_batches(question_type=qt)) 
            for qt in question_type_list
        )
        processed_batches = 0
        
        LOGGER.info(f"Starting parameter extraction for {contract_file_name}")
        
        for question_type in question_type_list:
            LOGGER.info(f"Extracting {question_type} parameters from contract")
            question_batches = self.create_question_batches(question_type=question_type)
            
            # Select appropriate prompt for question type
            if question_type == self.QUESTION_TYPE_QUALITATIVE:
                system_prompt = qual_parameter_prompt
            elif question_type == self.QUESTION_TYPE_QUANTITATIVE:
                system_prompt = quant_parameter_prompt
            elif question_type == self.QUESTION_TYPE_OTHER:
                system_prompt = other_parameter_prompt
            else:
                LOGGER.warning(f"Unknown question type: {question_type}, skipping")
                continue

            for batch_num, question_batch in enumerate(question_batches):
                try:
                    LOGGER.info(
                        f"Processing {question_type} batch {batch_num + 1}/{len(question_batches)}"
                    )
                    
                    # Prepare LLM prompt
                    batch_parameter_message[0]['content'] = system_prompt
                    batch_parameter_message[1]['content'][0]['text'] = (
                        f"## CONTRACT: \\n{input_contract_str} ## QUESTIONS: \\n {question_batch}"
                    )
                    
                    # Get LLM response
                    response_raw, _, _ = self.llm_client.get_response_with_token_tracking(
                        batch_parameter_message,
                        max_tokens_parameter=self.MAX_TOKENS_EXTRACTION,
                        doc_name=contract_file_name,
                        doc_type="MSA",
                        operation="contract_parameter_extraction",
                        page_number=-1
                    )
                    
                    # Parse JSON response with error handling
                    response_json = self.extract_clean_json(response_raw)
                    
                    # Validate response structure
                    vendor_name = response_json.get('vendor_name', 'UNKNOWN_VENDOR')
                    if vendor_name == 'UNKNOWN_VENDOR':
                        LOGGER.warning(
                            f"Missing 'vendor_name' in LLM response for {contract_file_name}"
                        )
                    
                    answers = response_json.get('answers', {})
                    if not answers:
                        LOGGER.warning(
                            f"No answers in LLM response for {question_type} batch {batch_num + 1}"
                        )
                        continue
                    
                    LOGGER.debug(f"Extracting {len(answers)} answers for {vendor_name}")
                    
                    # Process each answer in the batch
                    for question_id, value in answers.items():
                        try:
                            # Extract common fields with defaults
                            question_text = value.get('question', '')
                            relevant_context = value.get('relevant_context', '')
                            answer_justification = value.get('justification', '')
                            confidence_score = value.get('confidence_score', 0)
                            
                            # Extract type-specific answer fields
                            if question_type == self.QUESTION_TYPE_QUALITATIVE:
                                structured_answer = value.get('structured_answer', self.ANSWER_NOT_SPECIFIED)
                                unit = self.UNIT_NOT_APPLICABLE
                            elif question_type == self.QUESTION_TYPE_QUANTITATIVE:
                                structured_answer = value.get('numeric_answer', self.ANSWER_NOT_SPECIFIED)
                                unit = value.get('unit', '')
                            elif question_type == self.QUESTION_TYPE_OTHER:
                                structured_answer = value.get('answer', self.ANSWER_NOT_SPECIFIED)
                                unit = self.UNIT_NOT_APPLICABLE
                            else:
                                LOGGER.warning(f"Unknown question type: {question_type}")
                                continue
                            
                            # Add record to collection
                            parameter_records.append({
                                'category_name': "category_name",  # TODO: Extract from contract or config
                                'vendor_name': vendor_name,
                                'question_type': question_type,
                                'question_id': question_id,
                                'question_text': question_text,
                                'relevant_context': relevant_context,
                                'structured_answer': structured_answer,
                                "unit": unit,
                                'answer_justification': answer_justification,
                                "confidence_score": confidence_score
                            })
                            
                        except Exception as e:
                            LOGGER.error(
                                f"Error processing answer for question {question_id}: {e}"
                            )
                            # Continue processing other answers
                            continue
                    
                    # Update progress
                    processed_batches += 1
                    progress = 0.4 + (0.3 * processed_batches / total_batches)
                    if self.progress_callback:
                        self.progress_callback(
                            f"Extracted {question_type} parameters ({processed_batches}/{total_batches} batches)",
                            progress
                        )
                    
                except Exception as e:
                    LOGGER.error(
                        f"Error processing {question_type} batch {batch_num + 1}: {e}"
                    )
                    # Continue with next batch
                    continue
        
        # Create DataFrame from collected records (much faster than row-by-row append)
        self.parameter_from_contract_df = pd.DataFrame(parameter_records)
        LOGGER.info(f"Extracted {len(parameter_records)} parameters from contract")
        
        if self.progress_callback:
            self.progress_callback("Parameter extraction complete", 0.7)

    def score_qual_answer(self, answer: Any) -> Optional[float]:
        """Assign a score to a qualitative answer based on scoring rubric.
        
        Args:
            answer: Categorical answer ("YES", "NO", "CONDITIONAL", "NOT_SPECIFIED")
            
        Returns:
            Score if rule matched, None otherwise
        """
        answer = str(answer).upper()
        for rule in qual_scoring_rubric["qual_rules"]:
            if "value" in rule and answer == rule["value"]:
                LOGGER.debug(f"Matched qualitative rule: {answer} -> score {rule['score']}")
                return rule["score"]
        
        LOGGER.warning(f"No scoring rule matched for qualitative answer: {answer}")
        return None

    def score_quant_answer(
        self, 
        answer: Any, 
        question_id: str, 
        unit: str, 
        not_specified_flag: str
    ) -> Optional[float]:
        """Assign a score to a quantitative answer based on scoring rubric.
        
        Args:
            answer: Numeric answer or "NOT_SPECIFIED"
            question_id: Question identifier (e.g., "Q18")
            unit: Unit string ("months", "USD", "%", etc.)
            not_specified_flag: "NOT_SPECIFIED" if answer missing
            
        Returns:
            Score if rule matched, None otherwise
        """
        rules = quant_scoring_rubric.get(question_id, [])

        # Handle missing answers
        if str(answer).upper() == self.ANSWER_NOT_SPECIFIED or not_specified_flag == self.ANSWER_NOT_SPECIFIED:
            for rule in rules:
                if rule.get("rule") == "missing":
                    LOGGER.debug(f"{question_id}: Answer not specified, score {rule['score']}")
                    return rule["score"]
            LOGGER.warning(f"{question_id}: No 'missing' rule found for NOT_SPECIFIED answer")
            return None

        # Convert to numeric
        try:
            val = float(answer)
        except (ValueError, TypeError) as e:
            LOGGER.warning(f"Non-numeric answer '{answer}' for question {question_id}: {e}")
            return None

        # Apply scoring rules
        for rule in rules:
            if "min" in rule and "max" in rule:
                if rule["min"] <= val < rule["max"]:
                    LOGGER.debug(f"{question_id}: {val} in range [{rule['min']}, {rule['max']}), score {rule['score']}")
                    return rule["score"]
            elif "min" in rule and "max" not in rule:
                if val >= rule["min"]:
                    LOGGER.debug(f"{question_id}: {val} >= {rule['min']}, score {rule['score']}")
                    return rule["score"]
            elif "max" in rule and "min" not in rule:
                if val <= rule["max"]:
                    LOGGER.debug(f"{question_id}: {val} <= {rule['max']}, score {rule['score']}")
                    return rule["score"]

        LOGGER.warning(f"{question_id}: No scoring rule matched for value {val} {unit}")
        return None
    
    def rationalize_answers(self) -> None:
        """Process and normalize extracted answers for scoring.
        
        Converts quantitative answers to numeric, detects NOT_SPECIFIED patterns,
        and prepares data for scoring. Results update self.parameter_from_contract_df.
        """
        LOGGER.info("Rationalizing extracted answers")
        
        parameter_from_contract_df = self.parameter_from_contract_df.copy()
        parameter_from_contract_df["structured_answer_revised"] = parameter_from_contract_df["structured_answer"]
        
        # Convert quantitative answers to numeric
        parameter_from_contract_df.loc[
            parameter_from_contract_df["question_type"] == self.QUESTION_TYPE_QUANTITATIVE, 
            "structured_answer_revised"
        ] = pd.to_numeric(
            parameter_from_contract_df.loc[
                parameter_from_contract_df["question_type"] == self.QUESTION_TYPE_QUANTITATIVE, 
                "structured_answer_revised"
            ], 
            errors="coerce"
        )
        
        # Detect NOT_SPECIFIED pattern in answers
        parameter_from_contract_df["not_specified_flag"] = parameter_from_contract_df['structured_answer'].str.contains(
            r'not.*specified', 
            case=False, 
            na=False, 
            regex=True
        ).map({True: self.ANSWER_NOT_SPECIFIED, False: ''})
        
        # Mark answers as NOT_SPECIFIED where flag is set
        parameter_from_contract_df.loc[
            parameter_from_contract_df["not_specified_flag"] == self.ANSWER_NOT_SPECIFIED, 
            "structured_answer_revised"
        ] = self.ANSWER_NOT_SPECIFIED
        
        self.parameter_from_contract_df = parameter_from_contract_df
        LOGGER.info(f"Rationalized {len(parameter_from_contract_df)} answers")

    def score_contract_answers(self) -> None:
        """Apply scoring rubrics to extracted contract parameters.
        
        Scores qualitative and quantitative answers using respective rubrics.
        Merges with question metadata (Header_1, parameter names).
        Results stored in self.contract_parameter_scores_df.
        """
        LOGGER.info("Scoring contract answers")
        
        contract_parameter_scores_df = self.parameter_from_contract_df.copy()
        contract_parameter_scores_df["score"] = np.nan
        contract_parameter_scores_df["score_flag"] = ""
        
        # Score quantitative answers
        contract_parameter_scores_df["score"] = contract_parameter_scores_df.apply(
            lambda row: self.score_quant_answer(
                row["structured_answer_revised"], 
                row["question_id"], 
                row["unit"], 
                row["not_specified_flag"]
            ) if row["question_type"] == self.QUESTION_TYPE_QUANTITATIVE else row["score"], 
            axis=1
        )
        
        # Score qualitative answers
        contract_parameter_scores_df["score"] = contract_parameter_scores_df.apply(
            lambda row: self.score_qual_answer(row["structured_answer_revised"]) 
            if row["question_type"] == self.QUESTION_TYPE_QUALITATIVE else row["score"], 
            axis=1
        )
        
        # Mark unscored answers as exceptions (excluding 'other' type)
        contract_parameter_scores_df.loc[
            (contract_parameter_scores_df["question_type"] != self.QUESTION_TYPE_OTHER) & 
            (contract_parameter_scores_df["score"].isnull()), 
            ["score", "score_flag"]
        ] = (1, "exception")
        
        # Merge with question metadata
        try:
            contract_parameter_scores_df = contract_parameter_scores_df.merge(
                self.contract_questions_df[["Question_ID", "Header_1", "parameter"]], 
                left_on="question_id", 
                right_on="Question_ID", 
                how="left"
            )
            contract_parameter_scores_df.drop(columns=["Question_ID"], inplace=True)
        except Exception as e:
            LOGGER.error(f"Error merging question metadata: {e}")
            raise
        
        self.contract_parameter_scores_df = contract_parameter_scores_df
        
        # Log scoring summary
        total_scored = len(contract_parameter_scores_df)
        low_scores = len(contract_parameter_scores_df[contract_parameter_scores_df["score"] < 2])
        LOGGER.info(f"Scored {total_scored} parameters, {low_scores} with score < 2")
        
        if self.progress_callback:
            self.progress_callback(f"Scoring complete: {low_scores} low-score parameters", 0.85)

    def assess_contract(self) -> None:
        """Generate assessment report for low-scoring contract parameters.
        
        Identifies parameters with score < 2, formats them as JSON, and sends to
        LLM for detailed assessment. Results stored in self.contract_assessment_response_str.
        """
        LOGGER.info("Generating contract assessment")
        
        contract_parameter_scores_df = self.contract_parameter_scores_df
        low_score_rows = contract_parameter_scores_df[contract_parameter_scores_df["score"] < 2]
        
        if low_score_rows.empty:
            LOGGER.info("No low score parameters to assess - contract meets all criteria")
            self.contract_assessment_response_str = "No low score rows to assess."
            if self.progress_callback:
                self.progress_callback("Assessment complete: No issues found", 1.0)
            return

        # Format low-score parameters for LLM assessment
        assessments = [{
            "vendor_name": low_score_rows["vendor_name"].iloc[0] if not low_score_rows.empty else "",
            "category_name": low_score_rows["category_name"].iloc[0] if not low_score_rows.empty else "",
            "parameters_to_review": low_score_rows[
                ['question_id', 'parameter', 'Header_1', 'structured_answer_revised', 'answer_justification']
            ].to_dict(orient='records')
        }]

        input_low_score_rows_str = json.dumps(assessments, indent=4)
        LOGGER.debug(f"Assessing {len(low_score_rows)} low-score parameters")
        
        try:
            # Get assessment from LLM
            contract_assessment_message = self.contract_assessment_message(input_low_score_rows_str)
            contract_assessment_response_str, _, _ = self.llm_client.get_response_with_token_tracking(
                contract_assessment_message, 
                max_tokens_parameter=self.MAX_TOKENS_ASSESSMENT, 
                doc_name=os.path.basename(self.input_contract_path), 
                doc_type="MSA", 
                operation="contract_assessment", 
                page_number=-1
            )
            
            self.contract_assessment_response_str = contract_assessment_response_str
            LOGGER.info(f"Generated assessment for {len(low_score_rows)} low-score parameters")
            
            if self.progress_callback:
                self.progress_callback(f"Assessment complete: {len(low_score_rows)} issues reviewed", 1.0)
                
        except Exception as e:
            LOGGER.error(f"Error generating contract assessment: {e}")
            raise

    def process_pdf_contract(self) -> None:
        """Execute complete contract assessment workflow.
        
        Orchestrates the full pipeline:
        1. Convert PDF to text (or load test file)
        2. Extract parameters from contract text
        3. Rationalize and normalize answers
        4. Score answers against rubrics
        5. Generate assessment for low-scoring parameters
        
        Results stored in instance attributes (contract_text_str, parameter_from_contract_df,
        contract_parameter_scores_df, contract_assessment_response_str).
        
        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If any processing step fails
        """
        LOGGER.info(f"Starting contract processing workflow (test_file={self.use_test_file})")
        
        try:
            # Step 1: Get contract text
            if self.use_test_file:
                LOGGER.info("Using pre-converted test contract file")
                test_contract_path = TEST_CONTRACT_FILE_PATH
                
                try:
                    with open(test_contract_path, 'r', encoding='utf-8') as file:
                        self.contract_text_str = file.read()
                    LOGGER.info(f"Loaded test contract: {len(self.contract_text_str)} characters")
                except FileNotFoundError:
                    LOGGER.error(f"Test contract file not found: {test_contract_path}")
                    raise
                except Exception as e:
                    LOGGER.error(f"Error reading test contract file: {e}")
                    raise
                    
                if self.progress_callback:
                    self.progress_callback("Loaded test contract", 0.4)
            else:
                # Convert PDF to text
                self.convert_pdf_to_text()
            
            # Step 2: Extract parameters from contract
            self.extract_parameter_from_contract()
            
            # Step 3: Rationalize answers
            self.rationalize_answers()
            
            # Step 4: Score answers
            self.score_contract_answers()
            
            # Step 5: Generate assessment
            self.assess_contract()
            
            LOGGER.info("Contract processing workflow completed successfully")
            
        except Exception as e:
            LOGGER.error(f"Contract processing workflow failed: {e}")
            raise