import os

def choice():
    choose = input("How would you like to open the model? (API Key; .gguf)\n\nANS: ")
    
    if choose.lower() == "api key":
        api_key = input("\nPaste your OpenAI API Key here:\n\nKEY: ")
        return "api", api_key
        
    elif choose.lower() == ".gguf":
        model_key = input("\nPaste directory to your .gguf file here:\n\nPATH: ")
        return "local", model_key
    
    else:
       print("Invalid choice. Please restart.")
       return None, None 

if __name__ == "__main__":
    print("This is the choice.py file.")