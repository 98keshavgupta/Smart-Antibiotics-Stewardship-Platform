import random

def get_mock_guidelines(disease, microorganism):
    sources = [
        {"name": "WHO Guidelines", "url": "https://www.who.int/"},
        {"name": "CDC Stewardship", "url": "https://www.cdc.gov/"},
        {"name": "ICMR India", "url": "https://www.icmr.gov.in/"},
        {"name": "NCBI PubMed", "url": "https://pubmed.ncbi.nlm.nih.gov/"}
    ]
    
    results = []
    selected = random.sample(sources, k=2)
    
    for source in selected:
        results.append({
            "source": source['name'],
            "title": f"Guidelines for {disease} - {source['name']} 2024",
            "link": source['url']
        })
        
    return results

def get_live_research_data(disease, microorganism):
    aggregated_data = {"query": f"{disease} caused by {microorganism}", "results": []}
    
    other_papers = get_mock_guidelines(disease, microorganism)
    aggregated_data["results"].extend(other_papers)
    
    if not aggregated_data["results"]:
        aggregated_data["results"].append({
            "source": "Global Health Database",
            "title": f"Standard Therapy for {disease}",
            "link": "#"
        })
        
    return aggregated_data