"""
Test framework for evaluating RAG pipeline responses against expected solutions.

This module provides functionality to:
1. Load test cases from testcases.json
2. Submit queries to the RAG system
3. Compare responses with expected solutions using OpenAI
4. Generate success rate summaries
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

import pytest
from django.test import Client
from openai import OpenAI
from pydantic import BaseModel
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured OpenAI responses
class CriterionScore(BaseModel):
    """Score for a single evaluation criterion."""
    name: str
    score: int  # 0-10
    explanation: str

class OpenAIEvaluation(BaseModel):
    """Structured evaluation response from OpenAI."""
    overall_score: int  # 0-10
    is_satisfactory: bool
    criteria_scores: List[CriterionScore]
    strengths: List[str]
    weaknesses: List[str]
    explanation: str
    recommendation: str  # "pass" or "fail"

@dataclass
class TestCaseResult:
    """Result of a single test case evaluation."""
    test_id: str
    description: str
    query: str
    system_response: str
    expected_solution: str
    openai_evaluation: Dict[str, Any]
    is_successful: bool
    error_message: str = ""
    execution_time: float = 0.0

@dataclass 
class TestSummary:
    """Summary of all test case results."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    success_rate: float
    average_execution_time: float
    timestamp: str
    detailed_results: List[TestCaseResult]

class RAGTestFramework:
    """Framework for testing RAG pipeline responses against expected solutions."""
    
    def __init__(self, testcases_file: str = None, openai_api_key: str = None):
        """
        Initialize the test framework.
        
        Args:
            testcases_file: Path to testcases.json file
            openai_api_key: OpenAI API key for evaluation
        """
        self.testcases_file = testcases_file or str(Path(__file__).parent / "testcases.json")
        self.openai_client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.client = Client()
        self.test_cases = []
        self.load_test_cases()
    
    def load_test_cases(self) -> None:
        """Load test cases from JSON file."""
        try:
            with open(self.testcases_file, 'r') as f:
                self.test_cases = json.load(f)
            logger.info(f"Loaded {len(self.test_cases)} test cases from {self.testcases_file}")
        except FileNotFoundError:
            logger.error(f"Test cases file not found: {self.testcases_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in test cases file: {e}")
            raise
    
    def submit_query_to_system(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Submit a query to the RAG system and get the response.
        
        Args:
            request_data: Request data to send to the pipeline
            
        Returns:
            Tuple of (response_data, success_flag)
        """
        try:
            response = self.client.post(
                '/custom_rag/execute/',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('success'):
                return response_data, True
            else:
                logger.error(f"System request failed: {response_data}")
                return response_data, False
                
        except Exception as e:
            logger.error(f"Error submitting query to system: {e}")
            return {"error": str(e)}, False
    
    def evaluate_with_openai(self, system_response: str, expected_solution: str, 
                           evaluation_criteria: List[str], query: str) -> Dict[str, Any]:
        """
        Use OpenAI Responses API to evaluate if the system response matches the expected solution.
        
        Args:
            system_response: The response from our RAG system
            expected_solution: The expected solution from test case
            evaluation_criteria: List of criteria to evaluate against
            query: Original query for context
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            criteria_text = "\n".join([f"- {criterion}" for criterion in evaluation_criteria])
            
            evaluation_prompt = f"""
You are an expert evaluator for a RAG (Retrieval Augmented Generation) system that provides SAP product recommendations and solutions.

**Original Query:** {query}

**System Response:** 
{system_response}

**Expected Solution:**
{expected_solution}

**Evaluation Criteria:**
{criteria_text}

Please evaluate whether the system response adequately addresses the query based on the expected solution and criteria.

Score each criterion from 0-10 where:
- 0-3: Poor/Inadequate 
- 4-6: Acceptable/Partial
- 7-8: Good/Comprehensive
- 9-10: Excellent/Exceptional

Consider the response as satisfactory if the overall score is 7 or above.
"""
            
            # Use the new Responses API with requests
            response = requests.post(
                "https://api.openai.com/v1/responses",
                json={
                    "model": "gpt-4o",
                    "input": evaluation_prompt,
                    "instructions": "You are an expert evaluator for RAG systems. Provide objective, detailed evaluations using the structured format.",
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "evaluation_result",
                                "strict": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "overall_score": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 10
                                        },
                                        "is_satisfactory": {
                                            "type": "boolean"
                                        },
                                        "criteria_scores": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "score": {
                                                        "type": "integer",
                                                        "minimum": 0,
                                                        "maximum": 10
                                                    },
                                                    "explanation": {"type": "string"}
                                                },
                                                "required": ["name", "score", "explanation"],
                                                "additionalProperties": False
                                            }
                                        },
                                        "strengths": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "weaknesses": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "explanation": {"type": "string"},
                                        "recommendation": {
                                            "type": "string",
                                            "enum": ["pass", "fail"]
                                        }
                                    },
                                    "required": [
                                        "overall_score", 
                                        "is_satisfactory", 
                                        "criteria_scores",
                                        "strengths", 
                                        "weaknesses", 
                                        "explanation", 
                                        "recommendation"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        }
                    },
                    "temperature": 0.1,
                    "max_output_tokens": 1500
                },
                headers={
                    "Authorization": f"Bearer {self.openai_client.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            response_data = response.json()
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response_data}")
            
            # Extract the structured response
            output = response_data.get("output", [])
            if not output or len(output) == 0:
                raise Exception("No output in OpenAI response")
            
            content = output[0].get("content", [])
            if not content or len(content) == 0:
                raise Exception("No content in OpenAI output")
            
            text_content = content[0].get("text", "")
            evaluation = json.loads(text_content)
            
            # Convert criteria scores to dictionary format for compatibility
            criteria_scores = {}
            criteria_explanations = {}
            for criterion in evaluation.get("criteria_scores", []):
                criteria_scores[criterion["name"]] = criterion["score"]
                criteria_explanations[criterion["name"]] = criterion["explanation"]
            
            evaluation_result = {
                "overall_score": evaluation.get("overall_score", 0),
                "is_satisfactory": evaluation.get("is_satisfactory", False),
                "criteria_scores": criteria_scores,
                "criteria_explanations": criteria_explanations,
                "strengths": evaluation.get("strengths", []),
                "weaknesses": evaluation.get("weaknesses", []),
                "explanation": evaluation.get("explanation", ""),
                "recommendation": evaluation.get("recommendation", "fail")
            }
            
            return evaluation_result
            
        except Exception as e:
            logger.error(f"Error in OpenAI evaluation: {e}")
            return {
                "overall_score": 0,
                "is_satisfactory": False,
                "error": str(e),
                "explanation": f"Evaluation failed due to error: {e}",
                "criteria_scores": {},
                "strengths": [],
                "weaknesses": [],
                "recommendation": "fail"
            }
    
    def run_single_test_case(self, test_case: Dict[str, Any]) -> TestCaseResult:
        """
        Run a single test case and return the result.
        
        Args:
            test_case: Test case data from JSON
            
        Returns:
            TestCaseResult with evaluation results
        """
        start_time = datetime.now()
        
        test_id = test_case["id"]
        description = test_case["description"]
        query = test_case["query"]
        request_data = test_case["request_data"]
        expected_solution = test_case["expected_solution"]
        evaluation_criteria = test_case.get("evaluation_criteria", [])
        
        logger.info(f"Running test case: {test_id} - {description}")
        
        # Submit query to system
        system_response_data, success = self.submit_query_to_system(request_data)
        
        if not success:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestCaseResult(
                test_id=test_id,
                description=description,
                query=query,
                system_response="",
                expected_solution=expected_solution,
                openai_evaluation={},
                is_successful=False,
                error_message=f"System request failed: {system_response_data}",
                execution_time=execution_time
            )
        
        # Extract the actual response text
        system_response = json.dumps(system_response_data.get("data", {}), indent=2)
        
        # Evaluate with OpenAI
        openai_evaluation = self.evaluate_with_openai(
            system_response=system_response,
            expected_solution=expected_solution,
            evaluation_criteria=evaluation_criteria,
            query=query
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        is_successful = openai_evaluation.get("is_satisfactory", False)
        
        return TestCaseResult(
            test_id=test_id,
            description=description,
            query=query,
            system_response=system_response,
            expected_solution=expected_solution,
            openai_evaluation=openai_evaluation,
            is_successful=is_successful,
            execution_time=execution_time
        )
    
    def run_all_test_cases(self) -> TestSummary:
        """
        Run all test cases and return summary of results.
        
        Returns:
            TestSummary with overall results
        """
        logger.info("Starting test case execution...")
        
        results = []
        total_execution_time = 0
        
        for test_case in self.test_cases:
            result = self.run_single_test_case(test_case)
            results.append(result)
            total_execution_time += result.execution_time
            
            # Log individual result
            status = "PASS" if result.is_successful else "FAIL"
            logger.info(f"Test {result.test_id}: {status} (took {result.execution_time:.2f}s)")
            
            if not result.is_successful and result.error_message:
                logger.warning(f"Error: {result.error_message}")
        
        # Calculate summary statistics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.is_successful)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        average_execution_time = total_execution_time / total_tests if total_tests > 0 else 0
        
        summary = TestSummary(
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            average_execution_time=average_execution_time,
            timestamp=datetime.now().isoformat(),
            detailed_results=results
        )
        
        logger.info(f"Test execution completed. Success rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        return summary
    
    def save_results_to_file(self, summary: TestSummary, output_file: str = None) -> None:
        """
        Save test results to a JSON file.
        
        Args:
            summary: TestSummary to save
            output_file: Path to output file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_results_{timestamp}.json"
        
        # Convert to serializable format
        results_data = {
            "summary": {
                "total_tests": summary.total_tests,
                "successful_tests": summary.successful_tests,
                "failed_tests": summary.failed_tests,
                "success_rate": summary.success_rate,
                "average_execution_time": summary.average_execution_time,
                "timestamp": summary.timestamp
            },
            "detailed_results": []
        }
        
        for result in summary.detailed_results:
            results_data["detailed_results"].append({
                "test_id": result.test_id,
                "description": result.description,
                "query": result.query,
                "system_response": result.system_response,
                "expected_solution": result.expected_solution,
                "openai_evaluation": result.openai_evaluation,
                "is_successful": result.is_successful,
                "error_message": result.error_message,
                "execution_time": result.execution_time
            })
        
        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Results saved to: {output_file}")


# Pytest test functions
class TestRAGSystem:
    """Pytest test class for running RAG system tests."""
    
    @pytest.fixture(scope="class")
    def test_framework(self):
        """Create test framework instance."""
        return RAGTestFramework()
    
    def test_run_all_test_cases(self, test_framework):
        """Run all test cases and assert success rate meets threshold."""
        summary = test_framework.run_all_test_cases()
        
        # Save results
        test_framework.save_results_to_file(summary)
        
        # Print summary for visibility
        print(f"\n{'='*50}")
        print(f"TEST EXECUTION SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {summary.total_tests}")
        print(f"Successful: {summary.successful_tests}")
        print(f"Failed: {summary.failed_tests}")
        print(f"Success Rate: {summary.success_rate:.1f}%")
        print(f"Average Execution Time: {summary.average_execution_time:.2f}s")
        print(f"Timestamp: {summary.timestamp}")
        
        # Print individual results
        for result in summary.detailed_results:
            status = "✅ PASS" if result.is_successful else "❌ FAIL"
            score = result.openai_evaluation.get("overall_score", "N/A")
            print(f"\n{result.test_id}: {status} (Score: {score}/10)")
            print(f"  Query: {result.query[:100]}...")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            elif "explanation" in result.openai_evaluation:
                explanation = result.openai_evaluation["explanation"][:200]
                print(f"  Evaluation: {explanation}...")
        
        print(f"\n{'='*50}")
        
        # Assert that success rate meets minimum threshold (can be adjusted)
        min_success_rate = 70  # 70% minimum success rate
        assert summary.success_rate >= min_success_rate, \
            f"Success rate {summary.success_rate:.1f}% is below minimum threshold of {min_success_rate}%"
    
    def test_individual_test_cases(self, test_framework):
        """Run each test case individually for detailed debugging."""
        for test_case in test_framework.test_cases:
            result = test_framework.run_single_test_case(test_case)
            
            # Individual assertions for each test case
            assert result.system_response, f"Test {result.test_id}: No system response received"
            assert not result.error_message, f"Test {result.test_id}: {result.error_message}"
            
            # Optionally assert on OpenAI evaluation score
            if "overall_score" in result.openai_evaluation:
                score = result.openai_evaluation["overall_score"]
                assert score >= 5, f"Test {result.test_id}: Score {score}/10 is too low"


def main():
    """Main function to run tests from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG system test cases")
    parser.add_argument("--testcases", help="Path to testcases.json file")
    parser.add_argument("--output", help="Path to output results file")
    parser.add_argument("--openai-key", help="OpenAI API key")
    args = parser.parse_args()
    
    try:
        framework = RAGTestFramework(
            testcases_file=args.testcases,
            openai_api_key=args.openai_key
        )
        
        summary = framework.run_all_test_cases()
        framework.save_results_to_file(summary, args.output)
        
        print(f"\n🎯 Test Execution Complete!")
        print(f"📊 Success Rate: {summary.success_rate:.1f}% ({summary.successful_tests}/{summary.total_tests})")
        print(f"⏱️  Average Execution Time: {summary.average_execution_time:.2f}s")
        
        if summary.failed_tests > 0:
            print(f"❌ {summary.failed_tests} tests failed")
            exit(1)
        else:
            print("✅ All tests passed!")
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()