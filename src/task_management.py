import logging
import logging.config

from typing import Dict, List

import feedparser
import torch

from bs4 import BeautifulSoup
from functools import wraps
from time import time
from pydantic import HttpUrl
from transformers import (
    AutoConfig,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    pipeline,
)

from config import LANGUAGES, LANG_LEX_2_CODE
from logging_conf import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("src.task_management")


def proc_timer(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger.info(f"func:{f.__name__} args:[{args}, {kw}] took: {te - ts}:%2.4f sec")
        return result

    return wrapper


class TaskManager:
    """TaskManager class managing the summarization, translation,
    feed-parsing and other necessary processing tasks
    """

    def __init__(self):
        # The supported, by our application, translation languages
        self.supported_langs = LANGUAGES.values()

        # Load the bart-large-cnn model and tokenizer
        summarization_model_name = "facebook/bart-large-cnn"

        # Move model for summarization to GPU if available
        # self.summarization_device = (
        #     0 if torch.cuda.is_available() else -1
        # )  # 0 for GPU, -1 for CPU
        self.summarization_device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.summarization_config = AutoConfig.from_pretrained(summarization_model_name)

        self.summarizer = AutoModelForSeq2SeqLM.from_pretrained(
            summarization_model_name
        ).to(self.summarization_device)

        self.summarization_tokenizer = AutoTokenizer.from_pretrained(
            summarization_model_name
        )

        # Check if CUDA is available and set the device
        self.translation_device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Load translation pipeline for model facebook/nllb-200-distilled-1.3B
        self.translator = pipeline(
            "translation",
            model="facebook/nllb-200-distilled-1.3B",
            device=self.translation_device,
        )

    # @proc_timer
    def summarize(
        self, txt_to_summarize: str, max_length: int = 30, min_length: int = 10
    ) -> str:
        """Summarization task, used for summarizing the provided text

        Args:
            txt_to_summarize (str): the text that need to be summarized
            max_length (int, optional): the max_length downlimit of the summarized text. Defaults to 30.
            min_length (int, optional): the min_length downlimit of the summarized text. Defaults to 10.

        Returns:
            str: the summarized text
        """

        full_text_length = len(txt_to_summarize)

        # Adapt max and min lengths for summary, if larger than they should be
        max_perc_init_length = round(full_text_length * 0.3)
        max_length = (
            max_perc_init_length
            if self.summarization_config.max_length > 0.5 * full_text_length
            else max(max_length, self.summarization_config.max_length)
        )

        # Min length is the minimum of the following two:
        # the min to max default config values factor, multiplied by real max
        # the default config minimum value
        min_to_max_perc = (
            self.summarization_config.min_length / self.summarization_config.max_length
        )
        min_length = min(
            round(min_to_max_perc * max_length), self.summarization_config.min_length
        )

        # Tokenize input
        inputs = self.summarization_tokenizer(
            txt_to_summarize, return_tensors="pt", max_length=1024, truncation=True
        ).to(self.summarization_device)

        # Generate summary with custom max_length
        summary_ids = self.summarizer.generate(
            inputs["input_ids"],
            max_length=max_length,  # Set max_length here
            min_length=min_length,  # Set min_length here
            num_beams=4,  # Optional: Use beam search
            early_stopping=True,  # Optional: Stop early if EOS is reached
        )

        # Decode the summary
        summary_txt = self.summarization_tokenizer.decode(
            summary_ids[0], skip_special_tokens=True
        )

        return summary_txt

    # @proc_timer
    def translate(self, txt_to_translate: str, src_lang: str, tgt_lang: str) -> str:
        """Translate the provided text from a source language to a target language

        Args:
            txt_to_translate (str): the text to translate
            src_lang (str): the source language of the initial text
            tgt_lang (str): the target language the initial text should be translated to

        Raises:
            RuntimeError: error in case of unsupported source language
            RuntimeError: error in case of unsupported target language
            RuntimeError: error in case of translation failure

        Returns:
            str: the translated text
        """

        # Raise error in case of unsupported languages
        if src_lang not in self.supported_langs:
            raise RuntimeError("Unsupported source language.")
        if tgt_lang not in self.supported_langs:
            raise RuntimeError("Unsupported target language.")

        # Translate the text using the NLLB model
        src_lang = LANG_LEX_2_CODE.get(src_lang, src_lang)
        tgt_lang = LANG_LEX_2_CODE.get(tgt_lang, tgt_lang)
        translated_text = self.translator(
            txt_to_translate, src_lang=src_lang, tgt_lang=tgt_lang, batch_size=10
        )[0]["translation_text"]

        # If something goes wrong with the translation raise error
        if len(translated_text) <= 0:
            raise RuntimeError("Failed to generate translation.")

        return translated_text

    def parse_and_process_feed(
        self,
        rss_url: HttpUrl,
        src_lang: str,
        tgt_lang: str,
        entries_limit: int = None,
    ) -> List[Dict]:
        """Parse the input feed, and process the feed entries keeping the important information,
        summarizing and translating it

        Args:
            rss_url (HttpUrl): the feed url to parse
            src_lang (str): the feed's initial language
            tgt_lang (str): the target language to which the content will be translated
            entries_limit (int, optional): the number of feed-entries to be processed. Defaults to None (process all).

        Returns:
            List[Dict]: a list of dictionaries, each one containing the processed info regarding
            title, author, content and link for the respective feed entry
        """

        src_lang = LANGUAGES.get(src_lang, src_lang)
        tgt_lang = LANGUAGES.get(tgt_lang, tgt_lang)
        default_lang = LANGUAGES.get("en", "en")

        feed = feedparser.parse(rss_url)

        # Return the maximum number of entries in case entries is None or exceeding entries length
        processed_entries = feed.entries[:entries_limit]

        # Iterate over each entry in the feed
        for entry in processed_entries:
            title = entry.get("title", "")
            author = entry.get("author", "")
            link = entry.get("link", "")
            content = entry.get(
                "summary", entry.get("content", entry.get("description", ""))
            )

            soup = BeautifulSoup(content, features="html.parser")
            content = "".join(soup.findAll(text=True))

            # If source language is not English, first translate it to English to summarize
            if src_lang != default_lang:
                content = self.translate(
                    content, src_lang=src_lang, tgt_lang=default_lang
                )

            # Summarize the content
            summarized_content = self.summarize(content, max_length=30, min_length=10)

            # Translate the title and summarized content
            translated_title = self.translate(
                title, src_lang=src_lang, tgt_lang=tgt_lang
            )

            # Unless the target language is already the default, translate it
            translated_content = (
                self.translate(
                    summarized_content, src_lang=default_lang, tgt_lang=tgt_lang
                )
                if tgt_lang != default_lang
                else summarized_content
            )

            # Update entry
            entry.update(
                {
                    "title": translated_title,
                    "content": translated_content,
                    "author": author,
                    "link": link,
                }
            )

        return processed_entries
