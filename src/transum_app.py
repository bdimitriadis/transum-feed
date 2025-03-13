import gradio as gr

# import spaces

from typing import Dict, List, Tuple
from pydantic import HttpUrl

from task_management import TaskManager
from config import LANGUAGES


# Gradio interface
# @spaces.GPU
def process_rss(
    rss_url: HttpUrl,
    source_lang: str,
    target_lang: str,
    entries_limit: int = None,
) -> List[Dict]:
    """The wrapper to the respective task management function to retrieve the
    summarized and translated entries from the feed

    Args:
        rss_url (HttpUrl): the url
        src_lang (str): _description_
        tgt_lang (str): _description_
        entries_limit (int, optional): _description_. Defaults to None.

    Raises:
        gr.Error: _description_

    Returns:
        List[Dict]: _description_
    """
    try:
        tm = TaskManager()
        processed_entries = tm.parse_and_process_feed(
            rss_url, source_lang, target_lang, entries_limit
        )
    except Exception as e:
        raise gr.Error(e)

    return processed_entries, len(processed_entries)


# Custom css
custom_css = """
#messOut textarea {
    font-weight: bold;
}

#entriesTab {
    background-color: white;
}
"""

# Create a scrollable Markdown component
with gr.Blocks(
    theme=gr.themes.Soft(),
    css=custom_css,
) as demo:
    # Add a title using Markdown
    gr.Markdown("# RSS Feed Summarizer and Translator")

    # Add a description using Markdown
    gr.Markdown(
        "Input an RSS feed URL and specify the source and target languages to get summarized and translated content."
    )

    rss_entries = gr.State([])

    with gr.Row():
        # Step for starting points and options' steps for entries' dropdowns (retrieve and view)
        step = 5

        with gr.Column():
            rss_url = gr.Textbox(label="RSS Feed URL")

            languages_lst = LANGUAGES.keys()

            source_lang = gr.Dropdown(
                choices=languages_lst,
                value="",
                label="Source Language",
            )
            target_lang = gr.Dropdown(
                choices=languages_lst,
                value="",
                label="Target Language",
            )

            options_lst = list(range(5, 205, 5))
            entries_to_retrieve = gr.Dropdown(
                choices=options_lst,
                value=options_lst[0],
                label="Max Entries To Retrieve",
            )

            with gr.Row():
                clear_btn = gr.ClearButton(value="Clear")  # Clear button
                submit_btn = gr.Button("Submit", variant="primary")

        with gr.Column():
            # Message for feed entries retrieved and spinner purposes
            message_output = gr.Textbox(
                label="Entries Retrieved: ",
                interactive=False,
                elem_id="messOut",
            )

            def submit_request(
                feed_url: HttpUrl,
                src_lang: str,
                tgt_lang: str,
                entries_limit: int,
                latest_entries_num: int,
            ) -> Tuple[List[Dict], int, str]:
                """Calls format_processed_entries and format_processed_entries,
                everytime submit button is pressed in order to retrieve feed entries,
                format them and show them in the respective output component

                Args:
                    feed_url (HttpUrl): the feed url
                    src_lang (str): source language
                    tgt_lang (str): target_language
                    entries_limit (int): the entries' limit (to retrieve)
                    latest_entries_num (int): the number of the latest entries retrieved (if submission button has been pressed before)

                Returns:
                    Tuple[List[Dict], int, str]: the feed entries retrieved, the number of those entries, the entries properly formatted
                """

                proc_entries, entries_num = process_rss(
                    feed_url, src_lang, tgt_lang, entries_limit
                )
                # entries_updated = update_entries(latest_entries_num)
                formatted_updated_entries = format_processed_entries(proc_entries)
                return proc_entries, entries_num, formatted_updated_entries

            with gr.Tab("Feed Summaries:", visible=True, elem_id="entriesTab"):
                # Create a scrollable Markdown component
                markdown_output = gr.Markdown(height="400px")

                entries_to_view = gr.Dropdown(
                    choices=[options_lst[0]],
                    value=options_lst[0],
                    label="Max Entries To View",
                )

                @gr.on(
                    [entries_to_view.change],
                    inputs=[
                        rss_entries,
                        entries_to_view,
                    ],
                    outputs=[markdown_output],
                )
                def format_processed_entries(
                    processed_entries: List[Dict], entries_limit: int = None
                ) -> str:
                    """Format the output entries

                    Args:
                        processed_entries (List[Dict]): the entries retrieved from the feed that have been processed
                        entries_limit (int): a limit for the entries to view

                    Returns:
                        str: the formatted output containing the entries
                    """
                    entries_limit = entries_limit or len(processed_entries) or None

                    # Format the output for Gradio
                    output = ""
                    for entry in processed_entries[:entries_limit]:
                        output += f"### {entry.get('title', '---')}\n\n"
                        output += f"**Author:** {entry.get('author', '-')}\n\n"
                        output += f"{entry.get('content', '')}\n\n"
                        link = entry.get("link", "")
                        if link:
                            output += f"[Read more]({link})\n\n"
                        output += "---\n\n"

                    return output

                # Function to handle dropdown options for viewing entries
                @gr.on(
                    [rss_entries.change],
                    inputs=[rss_entries],
                    outputs=[entries_to_view],
                )
                def update_view_dropdown(view_entries: List[Dict]) -> gr.Dropdown:
                    """Update the options for view dropdown

                    Args:
                        view_entries (List[Dict]): the view entries list

                    Returns:
                        gr.Dropdown: a dropdown component with the updated options regarding view entries
                    """
                    max_entries_shown = len(view_entries) or None

                    # Update the dropdown options with the new length
                    dropdown_options = list(range(step, max_entries_shown + step, step))

                    # Return outputs to update components
                    return gr.Dropdown(
                        choices=dropdown_options,
                        value=entries_to_view.value,
                        label="Entries to view",
                    )

    # Link the function to the button
    submit_btn.click(
        submit_request,
        inputs=[rss_url, source_lang, target_lang, entries_to_retrieve, message_output],
        outputs=[rss_entries, message_output, markdown_output],
    )

    # Link the Clear button to reset inputs and outputs
    clear_btn.add(
        components=[
            rss_url,
            source_lang,
            target_lang,
            markdown_output,
            entries_to_view,
            entries_to_retrieve,
        ]
    )

# Launch the interface
demo.launch()
