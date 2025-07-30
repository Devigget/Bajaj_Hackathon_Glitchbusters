import requests
import json

# Test the FAISS-based RAG system
def test_faiss_rag():
    url = "http://127.0.0.1:8000/hackrx/run"
    
    # Test data
    test_request = {
        "documents": [
            "https://hackrx.blob.core.windows.net/assets/hackrx_6/policies/ICIHLIP22012V01222.pdf?sv=2023-01-03&st=2025-07-30T06%3A46%3A49Z&se=2025-09-01T06%3A46%3A00Z&sr=c&sp=rl&sig=9szykRKdGYj0BVm1skP%2BX8N9%2FRENEn2k7MQPUp33jyQ%3D"
        ],
        "questions": [
            "What is this document about?",
            "What are the key benefits mentioned?"
        ]
    }
    
    print("Testing FAISS-based RAG system...")
    print(f"Sending request to: {url}")
    print(f"Request data: {json.dumps(test_request, indent=2)}")
    
    try:
        response = requests.post(url, json=test_request, timeout=300)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! FAISS implementation working correctly.")
            print(f"Answers received: {len(result.get('answers', []))}")
            for i, answer in enumerate(result.get('answers', []), 1):
                print(f"Answer {i}: {answer[:200]}...")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_faiss_rag()
