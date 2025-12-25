import time
from datetime import datetime
import logging
import csv
import sys
import requests
from lxml import etree

log = logging.getLogger("bot")
log.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)


def get_node_value(xpath, tree):
	node = tree.xpath(xpath)
	if len(node):
		return str(node[0])
	else:
		return ""


def get_page_text(url, attempt=0):
	try:
		result = requests.get(url, headers={'User-Agent': user_agent}, timeout=5)
		return result.text
	except Exception as e:
		sleep_time = (attempt + 1) * 10
		log.warning(f"Exception requesting page: {url}. Attempt {attempt}. Sleeping {sleep_time}")
		log.warning(str(e))
		if attempt < 10:
			time.sleep(sleep_time)
			return get_page_text(url, attempt + 1)
		else:
			sys.exit(f"Exception requesting page: {url}")


if __name__ == "__main__":
	base_url = "https://scholarlycommons.pacific.edu/euler-works/"
	user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
	max_index = 866

	handle = open("euler.csv", 'w', encoding='UTF-8', newline='')
	writer = csv.writer(handle)
	writer.writerow(['Enestrom number','Latin title','English title','Language','Published As','Publish Date','Written Date','Original Source','Opera Omnia Citation','Link','Archive Notes','Content Summary'])
	for i in range(1, max_index + 1):
		page_url = f"{base_url}{i}/"
		page_text = get_page_text(page_url)
		tree = etree.fromstring(page_text, etree.HTMLParser())

		latin_title = get_node_value(f"//div[@id='title']/h1/a/text()", tree)
		if latin_title == "":
			latin_title = get_node_value(f"//div[@id='title']/h1/text()", tree)
		eng_title = get_node_value(f"//div[@id='eng_title']/p/text()", tree)
		authors = get_node_value(f"//div[@id='authors']/p/a/strong/text()", tree)
		inner_index_number = get_node_value(f"//div[@id='id_index_num']/p/text()", tree)
		language = get_node_value(f"//div[@id='language']/p/text()", tree)
		published_as = get_node_value(f"//div[@id='published_as']/p/text()", tree)
		publication_date = get_node_value(f"//div[@id='publication_date']/p/text()", tree)
		written_date = get_node_value(f"//div[@id='department']/p/text()", tree)
		source = get_node_value(f"//div[@id='source_pub_comp']/p/text()", tree)
		citation = get_node_value(f"//div[@id='oo_source_comp']/p/text()", tree)
		archive_notes = get_node_value(f"//div[@id='archive_notes']/p/text()", tree)
		content_summaries = get_node_value(f"//div[@id='contentsummaries']/p/text()", tree)

		if int(inner_index_number) != i:
			log.warning(f"Index doesn't match: {inner_index_number} : {i}")

		output_list = [str(i), latin_title, eng_title, language, published_as, publication_date, written_date, source, citation, page_url, archive_notes, content_summaries]
		#log.info(output_list)
		writer.writerow(output_list)

		time.sleep(0.1)
		log.info(f"{i}/{max_index}")

	handle.close()
