from typing import Dict, List, Optional
from search_engines import get_search_results
from get_google_search_links import get_google_search_links
from file_processor import process_file
from audio_processor import process_audio  # Import the audio processor
from link_processor import process_links

def scrape_and_process(
    query: str,
    translations: Dict[str, str],
    numero_pagine: int = 1,
    use_ollama: bool = True,
    use_cohere: bool = False,
    use_gpt: bool = False,
    use_gemini: bool = False,  # Aggiunto parametro per gemini
    search_engines: Optional[List[str]] = None,
    process_file_path: Optional[str] = None,
    process_audio_path: Optional[str] = None  # Added parameter for audio processing
) -> List[str]:
    output_files = {
        "scraped_texts": "files/scraped_texts.txt",
        "model_responses": "files/model_responses.txt",
        "model_output_no_link": "files/model_output_file_no_link.txt"
    }

    # Initialize output files
    for file_path in output_files.values():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("")

    results = []

    if process_file_path:
        # Process file instead of web scraping
        print(f"Processing file: {process_file_path}")
        process_file(
            process_file_path,
            translations.items(),
            output_files["scraped_texts"],
            use_ollama,
            use_cohere,
            use_gpt,
            use_gemini,  # Passo il parametro per gemini
        )
    elif process_audio_path:
        # Process audio file
        print(f"Processing audio file: {process_audio_path}")
        process_audio(
            process_audio_path,
            translations.items(),
            output_files["scraped_texts"],
            use_ollama,
            use_cohere,
            use_gpt,
            use_gemini,  # Passo il parametro per gemini
        )
    else:
        # Perform web scraping
        for language, translation in translations.items():
            print(f"{language.title()}: {translation}")

            if search_engines:
                for search_engine in search_engines:
                    print(f"Searching on {search_engine}...")
                    links = get_search_results(
                        translation,
                        search_engine,
                        numero_pagine
                    )
                    process_links(
                        links,
                        query,
                        output_files["scraped_texts"],
                        results,
                        use_ollama,
                        use_cohere,
                        use_gpt,
                        use_gemini,  # Passo il parametro per gemini
                    )
            else:
                # Use Google as fallback if no search engine is specified
                links = get_google_search_links(
                    translation,
                    numero_pagine
                )
                process_links(
                    links,
                    query,
                    output_files["scraped_texts"],
                    results,
                    use_ollama,
                    use_cohere,
                    use_gpt,
                    use_gemini,  # Passo il parametro per gemini
                )

    # Final output of responses
    print("Final result:", results)
    return results
