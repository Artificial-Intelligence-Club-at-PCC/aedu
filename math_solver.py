import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import google.api_core.exceptions # Import for handling exceptions

# --- Configuration ---
# Using your specific Project ID
project_id = 'hello-world-458205'

# Vertex AI documentation for model availability.
# Documentation: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
region = 'us-west1'

# --- Initialize Vertex AI ---
try:
    vertexai.init(project=project_id, location=region)
    print(f"Vertex AI initialized successfully for project '{project_id}' in region '{region}'")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")
    print("Please ensure:")
    print(f"1. Project ID '{project_id}' is correct.")
    print(f"2. Region '{region}' is correct and supports the intended model ('gemini-2.0-flash-001').")
    print("3. You have authenticated with Google Cloud (e.g., `gcloud auth application-default login`).")
    print("4. The Vertex AI API (aiplatform.googleapis.com) is enabled in your project.")
    print("5. Billing is enabled for your project.")
    exit() # Exit if initialization fails

def solve_math_problem(prompt):
    """
    Uses the specified Gemini model to solve a given math problem.
    """
    try:
        # --- Load the Gemini model ---
        # Using the desired 'gemini-2.0-flash-001' model ID
        model_name = "gemini-2.0-flash-001" # <--- USE THE NEW MODEL
        model = GenerativeModel(model_name)
        print(f"Attempting to use model: {model_name} in {region}")

        # --- Send the math problem to the model ---
        # Construct a prompt suitable for math problem solving
        full_prompt = f"Solve the following math problem step-by-step, showing your work:\n\nProblem: {prompt}\n\nSolution:"

        # Generate the content
        response = model.generate_content(full_prompt)

        # --- Return the model's response ---
        # Access the generated text content
        if response.candidates and response.candidates[0].content.parts:
            solution = response.candidates[0].content.parts[0].text
            return solution
        else:
            # Handle cases where the response might be empty or blocked (e.g., safety filters)
            print("Warning: Received an empty or potentially blocked response from the model.")
            # Log the reason if available
            try:
                # Use finish_reason (Enum) and check safety_ratings (list)
                finish_reason = response.candidates[0].finish_reason.name if response.candidates[0].finish_reason else "UNKNOWN"
                print(f"Finish Reason: {finish_reason}")
                if hasattr(response.candidates[0], 'safety_ratings') and response.candidates[0].safety_ratings:
                     print(f"Safety Ratings: {response.candidates[0].safety_ratings}")
                elif finish_reason == "SAFETY":
                     print("Response blocked due to safety filters.")
                elif finish_reason == "RECITATION":
                     print("Response blocked due to potential recitation.")

            except AttributeError:
                 # Handle cases where candidate or attributes might be missing
                 print("Could not retrieve detailed finish reason or safety ratings.")
            except Exception as e:
                 print(f"Error retrieving finish reason/safety ratings: {e}")

            print("Full Response Object (for debugging):", response)
            return "Model did not provide a solution. This could be due to safety filters, recitation filtering, or an empty response."

    # --- Error Handling ---
    except google.api_core.exceptions.NotFound as e:
        print(f"\n--- ERROR ---")
        print(f"Error: Model '{model_name}' not found in region '{region}' for project '{project_id}'.")
        print(f"Details: {e}")
        print("\nPlease verify:")
        print(f"1. The model name '{model_name}' is correct.")
        print(f"2. The region '{region}' supports this model according to the *latest* Google Cloud documentation.")
        print(f"3. Project '{project_id}' has access (check for allowlisting if using preview/new models).")
        print("Check Model Availability: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions")
        print("-------------")
        return None
    except google.api_core.exceptions.PermissionDenied as e:
        print(f"\n--- ERROR ---")
        print(f"Error: Permission denied. {e}")
        print(f"Please ensure the account running this script has the 'Vertex AI User' role (roles/aiplatform.user) or equivalent permissions on project '{project_id}'.")
        print("-------------")
        return None
    except google.api_core.exceptions.ResourceExhausted as e:
        print(f"\n--- ERROR ---")
        print(f"Error: Quota exceeded. {e}")
        print("You might have hit a rate limit or quota limit for the Vertex AI API. Check your quotas in the Google Cloud Console.")
        print("-------------")
        return None
    except google.api_core.exceptions.ServiceUnavailable as e:
        print(f"\n--- ERROR ---")
        print(f"Error: The Vertex AI service is temporarily unavailable. Retrying might help. {e}")
        print("-------------")
        return None # Or implement retry logic
    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR ---")
        print(f"An unexpected error occurred: {e}")
        print(f"Error Type: {type(e)}")
        # Consider logging the full traceback in a real application
        # import traceback
        # print(traceback.format_exc())
        print("-----------------------")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    math_problem = input("Enter your math problem: ")

    if math_problem:
        print("\nAttempting to solve...")
        solution = solve_math_problem(math_problem)

        if solution:
            print("\n--- Solution ---")
            print(solution)
            print("----------------")
        else:
            print("\nFailed to get solution due to errors mentioned above.")
    else:
        print("No math problem entered.")
