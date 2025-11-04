import requests
import sys
import json
from datetime import datetime

class PromptGeneratorAPITester:
    def __init__(self, base_url="https://prompt-wizard-193.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": None,
                "error": None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    result["error"] = error_data
                    print(f"   Error: {error_data}")
                except:
                    result["error"] = response.text
                    print(f"   Error: {response.text}")

            self.test_results.append(result)
            return success, result.get("response_data", {})

        except Exception as e:
            print(f"❌ Failed - Exception: {str(e)}")
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_form_prompt_generation(self):
        """Test form-based prompt generation"""
        form_data = {
            "subject": "luxury watch",
            "setting": "marble table",
            "lighting": "studio",
            "camera_angle": "45_degree",
            "style": "luxury",
            "mood": "sophisticated",
            "additional_details": "gold accents, premium materials"
        }
        return self.run_test("Form Prompt Generation", "POST", "prompts/generate-form", 200, form_data)

    def test_ai_prompt_enhancement(self):
        """Test AI prompt enhancement"""
        ai_data = {
            "basic_prompt": "a coffee cup on a wooden table"
        }
        return self.run_test("AI Prompt Enhancement", "POST", "prompts/enhance", 200, ai_data, timeout=60)

    def test_image_generation(self):
        """Test image generation with Nano Banana"""
        image_data = {
            "prompt": "Professional commercial photography of luxury watch in marble table, professional studio lighting, three-point lighting setup, shot at 45-degree angle, dynamic composition, luxury premium aesthetic, high-end feel, sophisticated atmosphere, captured with professional DSLR camera, 50mm lens, f/2.8 aperture, 8K resolution, ultra-detailed, photorealistic, sharp focus, professional color grading, commercial quality, no artificial elements, natural product placement, gold accents, premium materials"
        }
        return self.run_test("Image Generation", "POST", "prompts/generate-image", 200, image_data, timeout=120)

    def test_save_prompt(self):
        """Test saving prompt to history"""
        save_data = {
            "prompt_text": "Test prompt for saving",
            "prompt_type": "form",
            "parameters": {"subject": "test item"},
            "image_data": None
        }
        return self.run_test("Save Prompt", "POST", "prompts/save", 200, save_data)

    def test_get_history(self):
        """Test getting prompts history"""
        return self.run_test("Get History", "GET", "prompts/history", 200)

    def test_get_favorites(self):
        """Test getting favorite prompts"""
        return self.run_test("Get Favorites", "GET", "prompts/favorites", 200)

    def test_toggle_favorite(self, prompt_id):
        """Test toggling favorite status"""
        return self.run_test("Toggle Favorite", "POST", f"prompts/{prompt_id}/favorite", 200)

    def test_form_validation(self):
        """Test form validation - empty subject"""
        empty_data = {
            "subject": "",
            "setting": "",
            "lighting": "",
            "camera_angle": "",
            "style": "",
            "mood": "",
            "additional_details": ""
        }
        return self.run_test("Form Validation (Empty Subject)", "POST", "prompts/generate-form", 200, empty_data)

    def test_ai_validation(self):
        """Test AI enhancement validation - empty prompt"""
        empty_ai_data = {
            "basic_prompt": ""
        }
        return self.run_test("AI Validation (Empty Prompt)", "POST", "prompts/enhance", 200, empty_ai_data)

def main():
    print("🚀 Starting Master Prompt Generator API Tests")
    print("=" * 60)
    
    tester = PromptGeneratorAPITester()
    
    # Test basic connectivity
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ Root endpoint failed, stopping tests")
        return 1

    # Test form-based prompt generation
    success, form_response = tester.test_form_prompt_generation()
    generated_prompt = form_response.get('prompt', '') if success else ''

    # Test AI prompt enhancement
    success, ai_response = tester.test_ai_prompt_enhancement()

    # Test image generation (if we have a prompt)
    if generated_prompt:
        success, image_response = tester.test_image_generation()

    # Test saving prompt
    success, save_response = tester.test_save_prompt()
    saved_prompt_id = save_response.get('id', '') if success else ''

    # Test history and favorites
    tester.test_get_history()
    tester.test_get_favorites()

    # Test toggle favorite (if we have a saved prompt)
    if saved_prompt_id:
        tester.test_toggle_favorite(saved_prompt_id)

    # Test validation scenarios
    tester.test_form_validation()
    tester.test_ai_validation()

    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # Print failed tests
    failed_tests = [test for test in tester.test_results if not test['success']]
    if failed_tests:
        print("\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"   - {test['test_name']}: {test.get('error', 'Unknown error')}")
    
    # Save detailed results
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': tester.tests_run,
            'passed_tests': tester.tests_passed,
            'success_rate': (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0,
            'test_results': tester.test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/test_reports/backend_test_results.json")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())