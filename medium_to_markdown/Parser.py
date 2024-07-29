from datetime import datetime
from bs4 import BeautifulSoup, Tag, NavigableString

import requests
import shutil
import os
import re

class MediumParser:
    
    IMAGE_SEQUENCE = 0
    OUTPUT_DIR = "medium/origin_md"
    
    def __init__(self, url, output_dir = "medium/origin_md",
                 output_filename="", 
                 link_image_path="image",
                 is_image_download=False,
                 ssl_verify=True,
                 headers={'User-Agent': 'Mozilla/5.0'}):
        """
            Initialize a MediumParser object.

            Parameters:
            - url (str): The URL of the Medium article to convert to Markdown.
            - output_dir (str): The directory where the output Markdown file will be saved. Default is 'medium/origin_md'.
            - output_filename (str): The desired filename for the output Markdown file. If not provided, a default filename will be used.
            - link_image_path (str): The path to the image directory where the downloaded images will be saved. Default is 'image'.
            - is_image_download (bool): Flag indicating whether to download images referenced in the article. Default is False.
            - ssl_verify (bool): Flag indicating whether to verify SSL certificates when making requests. Default is False.
            - headers (dict): Custom headers to include in the HTTP requests. Default is {'User-Agent': 'Mozilla/5.0'}.
        """
        self.url = url
        self.is_image_download = is_image_download
        self.ssl_verify = ssl_verify
        self.headers = headers
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.title=""
        self.author=""
        self.output_filename=output_filename
        self.OUTPUT_DIR = output_dir
        self.link_image_path = link_image_path
        
        if self.output_filename != "":
            if self.output_filename.endswith(".md"):
                self.output_filename = self.output_filename[:-3]
                
            self.output_filename = f"{self.current_date}-{self.output_filename}"


    def parse(self,txt_html="",is_savefile=True,is_get_dom=False):
        """
        Parses the Medium post, saves it as a Markdown file, and returns True if successful, False otherwise.
        Parameters:
        - txt_html (str): The HTML content of the Medium article. If not provided, the content will be fetched from the URL.
        - is_save (bool): Flag indicating whether to save the output Markdown file. Default is True.
        """
        try:
            if txt_html:
                dom = BeautifulSoup(txt_html, 'html.parser')
            else:
                dom = self.get_dom(self.url)
            self.get_meta(dom)
            
            if self.output_filename == "":
                self.output_filename = re.sub(r'[<>:"/\\|?*]', '', self.title).replace(" ", "_")
                output_filename = f"{self.OUTPUT_DIR}/{self.current_date}-{self.output_filename}.md"
            else:
                output_filename = f"{self.OUTPUT_DIR}/{self.output_filename}.md"
                
            parsed_post = self.parse_medium_post(dom,is_savefile)
                
            if is_savefile:
                if not os.path.exists(os.path.dirname(output_filename)):
                    os.makedirs(os.path.dirname(output_filename))
                with open(output_filename, "w", encoding='utf-8') as f:
                    f.write(parsed_post)
                    
            if is_get_dom:
                return parsed_post,dom
            else:
                return parsed_post,None
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_dom(self,url):
        response = requests.get(url, verify=self.ssl_verify,headers=self.headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    
    def get_meta(self,dom):
        try:
            url_tag = dom.find('meta', {'property': 'og:url'})
            title_tag = dom.find('meta', {'name': 'title'})
            author_tag = dom.find('meta', {'name': 'author'})
            self.url = url_tag['content'] if self.url=="" else self.url
            self.title = title_tag['content'] if title_tag else ''
            self.author = author_tag['content'] if author_tag else ''
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        
    def parse_medium_post(self,dom,is_savefile):
        parsed_post = []
        
        for node in dom.children:
            content = self.parse_dom(node)
            if content:
                parsed_post.append(content)
        if is_savefile:
            parsed_post.insert(0, f"---\ntitle: {self.title}\nauthor: {self.author}\ndate: {self.current_date}\nurl: {self.url}\n---\n")
            return '\n'.join(parsed_post)
        else:
            return {"title":self.title,"author":self.author,"contents":'\n'.join(parsed_post),"date":self.current_date,"url":self.url}

    def parse_dom(self,node):
        parsed_content = []

        if isinstance(node, Tag):
            if node.name == "h1":
                text = self.extract_inline(node)
                if text:
                    parsed_content.append(f"\n# {text}\n")
            elif node.name == "h2":
                text = self.extract_inline(node)
                if text:
                    parsed_content.append(f"\n## {text}\n")
            elif node.name == "p":
                if 'pw-post-body-paragraph' in node.get('class', []):
                    text = self.extract_inline(node)
                    if text:
                        parsed_content.append(f"\n{text.strip()}\n")
            elif node.name == "li":
                text = self.extract_inline(node)
                if text:
                    parsed_content.append(f"\n- {text}\n\n")
            elif node.name == "pre":
                text = self.extract_inline(node)
                if text:
                    parsed_content.append(f"```\n{text}\n```\n")
            elif node.name == "source":
                links_str = node.get('srcset')
                if links_str:
                    links = links_str.split(" ")
                    link = next((link for link in links if 'webp' in link), None)
                    if link:
                        if self.is_image_download==False:
                            parsed_content.append(f"![Medium-Image]({link.strip()})\n")
                        else:
                            response = requests.get(link.strip(), stream=True,verify=self.ssl_verify,headers=self.headers)
                            if response.status_code == 200:

                                filename = f"{self.output_filename}_{self.IMAGE_SEQUENCE}.png"
                                local_image_path = f"{self.OUTPUT_DIR}/image/{filename}"
                                if not os.path.exists(os.path.dirname(local_image_path)):
                                    os.makedirs(os.path.dirname(local_image_path))
                                with open(local_image_path, 'wb') as out_file:
                                    shutil.copyfileobj(response.raw, out_file)
                                    
                                del response

                                parsed_content.append(f"![Medium-Image]({self.link_image_path}/{filename})\n")
                                self.IMAGE_SEQUENCE += 1
            else:
                for child in node.children:
                    child_content = self.parse_dom(child)
                    if child_content:
                        parsed_content.append(child_content)
        
        if parsed_content:
            return ''.join(parsed_content)
        else:
            return None

    def extract_inline(self,node):
        if isinstance(node, NavigableString):
            return node
        elif isinstance(node, Tag):
            if node.name in ["b", "strong"]:
                text = self.parse_formatting_text(node)
                return f"**{text.strip()}** "
            elif node.name in ["i", "em"]:
                text = self.parse_formatting_text(node)
                return f"*{text.strip()}* "
            elif node.name == "br":
                return "\n"
            elif node.name == "code":
                text = self.parse_formatting_text(node)
                return f"`{text.strip()}` "
            elif node.name == "a":
                text = self.parse_formatting_text(node)
                url = node.get('href')
                return f"[{text}]({url}) "
            else:
                text = self.parse_formatting_text(node)
                return text
        else:
            return None

    def parse_formatting_text(self,element):
        result = []
        for child in element.children:
            text = self.extract_inline(child)
            if text:
                result.append(text)
        return ''.join(result)