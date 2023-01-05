#!/usr/bin/python3
import requests
import json 
import trafilatura
import openai

def get_config():
    """ Loads the configurations from config.txt
    
    Returns:
        _dict_  : Configurations  
    """    

    config = {}
    with open('config.txt', 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            config[key] = value
    return config

def crawl_information(searchTerm,config):
    """ Fetches the top 5 links for the search term from Google 

    Args:
        searchTerm (_string_): Manufacturer name and part number sent as parameter to this program 
        config (_dict_): Configurations that holds google keys and search engine definition 

    Returns:
        _list_: List of top 5 URLs 
    """    
 
    url = config['searchURL']

    headers = {
    'Accept': 'application/json'
    }

    params = {
    "cx": str(config['searchEngineCx']),
    "q": searchTerm,
    "key": config['googleKey'],
    "num": "5"
    }

    response = requests.request("GET", url, headers=headers,params=params)

    searchResults = json.loads(response.text)["items"]

    resultURL = []
    for result in searchResults:
        resultURL.append(result["link"])
    
    return resultURL

def extract_product_data(resultURLs,config):
    """Extracts product data from the top links 

    Args:
        resultURLs (_list_): List of top 5 URLs
        config (_dict_): Configurations for extracting product data  

    Returns:
        _string_: Extracted product data from the top links 
    """        

    productData = " "

    for url in resultURLs: 
        productData += "\n"
        text = " "

        # Use trafilatura to extract text from the pages.
        try:
            downloaded  = trafilatura.fetch_url(url)
            text = trafilatura.extract(downloaded)
        except:
            #TODO understand the exceptions and handle them
            #for POC, we skip URLs with issues 
            continue
        

        # Skipping no data pages and pages where the text is less than 200 characters 
        # as the there is a maximum limit on tokens for the models 
        # refer to https://beta.openai.com/tokenizer for more details 
        if text != None and len(text) > 200:
            if (len(productData) + len(text)) < int(config['maxPromptChars']):
                productData += text
                #print(url) #Debug code
            else:
                #If adding the full prouct data from a page exceeds the prompt characters, then 
                #the data is trucated to the fit the list. 
                productData +=  text[:int(config['maxPromptChars'])-len(productData)]
                #Since completion API is used, the model tried to complete incomplete sentenses. 
                #so the below code removes the last incomplete sentence based on the \n 
                productData = productData.rsplit('\n', 1)[0]
                #print("last partial url:" , url)   #Debug code
                break 
            
    #print(productData)  #Debug code

    return productData

def generate_copy(productData,config):
    """ Generates the final product copy based on the product data gathered 

    Args:
        productData (_string_): Product data extracted from web 
        config (_dict_): Configurations for extracting GPT Model  

    Returns:
        _string_: Final product copy 
    """    
    
    openai.api_key = config['openAiKey']

    response = openai.Completion.create(
    model=config['gptModel'],
    prompt="Please generate a product description for that includes information about its features, benefits, and uses. The description should be written in a way that is engaging and persuasive to potential customers. avoid information on shipping and promotion details. You can use the following information as a starting point: \n" + productData ,
    temperature=float(config['temperature']),
    max_tokens=int(config['maxTokens']),
    top_p=float(config['top_p']),
    frequency_penalty=float(config['frequency_penalty']),
    presence_penalty=float(config['presence_penalty'])
    )

    return response

def main_func(search_parameter):
    """Main function

    Args:
        search_parameter (_string_):  Manufacturer name and part number 

    Returns:
        _string_: Final product copy
    """    
    config = get_config()
    resultURL = crawl_information(search_parameter,config)
    productData = extract_product_data(resultURL,config)
    copy = generate_copy(productData,config)
    return copy 

if __name__ == '__main__':
    search_parameter = "hamilton beach 29881"
    copy = main_func(search_parameter)
    print(copy)
