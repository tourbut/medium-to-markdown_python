from datetime import datetime
from bs4 import BeautifulSoup, Tag, NavigableString

import requests
import shutil
import os
import argparse

class MediumParser:
    
    IMAGE_SEQUENCE = 0
    OUTPUT_DIR = "medium/origin_md"
    
    def __init__(self, url, output_filename, is_image_download=False,ssl_verify=False):
        self.url = url
        self.output_filename = output_filename
        self.is_image_download = is_image_download
        self.ssl_verify = ssl_verify
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.title=""
        self.author=""
        
        if self.output_filename.endswith(".md"):
            self.output_filename = self.output_filename[:-3]
            
        self.output_filename = f"{self.current_date}-{self.output_filename[:-3]}"
        

    def parse_and_savefile(self):
        try:
            dom = self.get_dom(self.url)
            parsed_post = self.parse_medium_post(dom)
            output_filename = f"{self.OUTPUT_DIR}/{self.output_filename}.md"
            
            if not os.path.exists(os.path.dirname(output_filename)):
                os.makedirs(os.path.dirname(output_filename))
            
            with open(output_filename, "w",encoding='utf-8') as f:
                f.write(parsed_post)
                
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_dom(self,url):
        response = requests.get(url, verify=self.ssl_verify)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    def parse_medium_post(self,dom):
        parsed_post = []
        title_tag = dom.find('meta', {'name': 'title'})
        author_tag = dom.find('meta', {'name': 'author'})
        self.title = title_tag['content'] if title_tag else ''
        self.author = author_tag['content'] if author_tag else ''
        for node in dom.children:
            content = self.parse_dom(node)
            if content:
                parsed_post.append(content)
      
        parsed_post.insert(0, f"---\ntitle: {self.title}\nauthor: {self.author}\ndate: {self.current_date}\nurl: {self.url}\n---\n")
        return '\n'.join(parsed_post)

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
                            response = requests.get(link.strip(), stream=True,verify=self.ssl_verify)
                            if response.status_code == 200:

                                filename = f"{self.output_filename}_{self.IMAGE_SEQUENCE}.png"
                                local_image_path = f"{self.OUTPUT_DIR}/image/{filename}"
                                if not os.path.exists(os.path.dirname(local_image_path)):
                                    os.makedirs(os.path.dirname(local_image_path))
                                with open(local_image_path, 'wb') as out_file:
                                    shutil.copyfileobj(response.raw, out_file)
                                    
                                del response

                                parsed_content.append(f"![Medium-Image]({local_image_path})\n")
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

if __name__ == "__main__":
    print("Medium to Markdown Parser")
    print("Start parsing...")
    
    arg_parser = argparse.ArgumentParser(description="Medium to Markdown Parser")
    arg_parser.add_argument("--url", help="Medium post URL",required=True)
    arg_parser.add_argument("--filename", help="Output filename",required=True)
    arg_parser.add_argument("--is_image_download", help="Image download option(Y or N)", default="N",required=False)
    arg_parser.add_argument("--ssl_verify", help="SSL Verify option(Y or N)", default="N",required=False)
    args = arg_parser.parse_args()
    
    parser = MediumParser(args.url, args.filename, 
                            False if args.is_image_download.upper() == "N" else True, 
                            False if args.ssl_verify.upper() == "N" else True)
    
    if parser.parse_and_savefile():
        print("Parsing is done.")