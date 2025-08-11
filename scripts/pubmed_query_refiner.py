from .pubmed_query_agent import generate_pubmed_query
from .pubmed_api import search_pubmed
from .llm_client import call_llm
from .utils import deduplicate_papers

def iterative_pubmed_search(question, model="gpt-4o-mini", top_n=10):
    # Step 1: Generate initial query
    initial_query = generate_pubmed_query(question)
    print(f"Initial PubMed query: {initial_query}")
    
    # Step 2: Run first query
    first_results = search_pubmed(initial_query, max_results=top_n)
    
    # Step 3: Prepare context for refinement
    paper_summaries = "\n\n".join(
        [f"Title: {r['title']}\nAbstract: {r.get('abstract','No abstract')}" 
         for r in first_results]
    )
    
    refinement_prompt = f"""
    Given the research question: {question}
    And these top PubMed results:
    {paper_summaries}
    
    Suggest up to 3 improved or alternate PubMed Boolean queries
    that could find additional relevant papers not in the above list.
    Only return the Boolean queries, each on its own line.
    """
    
    # Step 4: Get refined queries
    refined_queries_text = call_llm(model, refinement_prompt)
    refined_queries = [q.strip() for q in refined_queries_text.split("\n") if q.strip()]
    
    # Step 5: Run each refined query
    all_results = first_results.copy()
    for q in refined_queries:
        print(f"Running refined query: {q}")
        new_results = search_pubmed(q, max_results=top_n)
        all_results.extend(new_results)
    
    # Step 6: Deduplicate
    all_results = deduplicate_papers(all_results)
    
    return all_results
