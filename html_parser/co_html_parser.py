from bs4 import BeautifulSoup, Doctype
import re
from datetime import datetime
from parser_base import ParserBase


class coParseHtml(ParserBase):
    def __init__(self, input_file_name):
        super().__init__()
        self.class_regex = {'ul': '^Art.', 'head2': '^ARTICLE ',
                            'title': '^(TITLE)|^(CONSTITUTION OF KENTUCKY)',
                            'sec_head': r'^\d+(\.\d+)*-\d+-\d+\.', 'part_head': '^PART\s\d+',
                            'junk': '^Annotations', 'ol': r'^(\(1\))', 'head4': '^ANNOTATION', 'nd_nav': '^1\.',
                            'Analysis': '^I\.'}
        self.title_id = None
        self.soup = None
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.html_file_name = input_file_name

        self.watermark_text = """Release {0} of the Official Code of Colorado Annotated released {1}.
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
        This document is not subject to copyright and is in the public domain.
        """

        self.start_parse()

    def create_page_soup(self):

        """
        - Read the input html to parse and convert it to Beautifulsoup object
        - Input Html will be html 4 so replace html tag which is self.soup.contents[0] with <html>
          which is syntax of html tag in html 5
        - add attribute 'lang' to html tag with value 'en'
        :return:
        """

        with open(f'../transforms/co/occo/r{self.release_number}/raw/{self.html_file_name}') as open_file:
            html_data = open_file.read()
        self.soup = BeautifulSoup(html_data, features="lxml")
        self.soup.contents[0].replace_with(Doctype("html"))
        self.soup.html.attrs['lang'] = 'en'
        print('created soup')

    def get_class_name(self):

        """
                    - Find the textutil generated class names for each type of tag (h1, h2, ....)
                      using re pattern specified in self.tag_type_dict
        """
        for key, value in self.class_regex.items():
            tag_class = self.soup.find(
                lambda tag: tag.name == 'p' and re.search(self.class_regex.get(key), tag.get_text().strip()) and
                            tag.attrs["class"][0] not in self.class_regex.values())
            if tag_class:
                self.class_regex[key] = tag_class.get('class')[0]

        print(self.class_regex)
        print('updated class dict')

    def remove_junk(self):
        """
                 - Delete the junk tags (empty tags,span tags and unwanted meta tags)
                 - Add new meta tags for storing release related information of parsed html
                 - Rename <br> tags
             """

        [text_junk.decompose() for text_junk in self.soup.find_all("p", class_=self.class_regex["junk"])]

        [text_junk.decompose() for text_junk in self.soup.find_all("span", class_="Apple-converted-space")]

        for meta in self.soup.findAll('meta'):
            if meta.get('name') and meta.get('name') in ['Author', 'Description']:
                meta.decompose()

        for key, value in {'viewport': "width=device-width, initial-scale=1",
                           'description': self.watermark_text.format(self.release_number, self.release_date,
                                                                     datetime.now().date())}.items():
            new_meta = self.soup.new_tag('meta')
            new_meta.attrs['name'] = key
            new_meta.attrs['content'] = value
            self.soup.head.append(new_meta)

        print('junk removed')

    def set_appropriate_tag_name_and_id(self, tag_name, header_tag, chap_nums, prev_id, sub_tag, class_name):
        if re.search('constitution', self.html_file_name):
            header_tag.name = tag_name
            header_tag.attrs = {}
            header_tag["class"] = class_name
            if prev_id:
                header_tag['id'] = f"{prev_id}{sub_tag}{chap_nums}"
            else:
                title_id = header_tag.find_previous("h1").get('id')
                header_tag['id'] = f"{title_id}{sub_tag}{chap_nums}"

        else:
            header_tag.name = tag_name
            header_tag.attrs = {}
            header_tag["class"] = class_name
            if prev_id:
                header_tag['id'] = f"{prev_id}{sub_tag}{chap_nums}"
            else:
                title_id = header_tag.find_previous("h1").get('id')
                header_tag['id'] = f"{title_id}{sub_tag}{chap_nums}"

    def replace_tags(self):
        snav = 0
        cnav = 0
        anav = 0
        pnav = 0
        chapter_id_list = []
        header_list = []
        note_list = []
        cur_id_list = []
        repeated_header_list = []
        analy_ul_tag = self.soup.new_tag("ul")
        count = 1
        for header_tag in self.soup.body.find_all():
            if re.search('constitution', self.html_file_name):

                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search('constitution\.us', self.html_file_name):
                        self.title_id = "constitution-us"
                    else:
                        self.title_id = "constitution-co"

                    header_tag.name = "h1"
                    header_tag.attrs = {}
                    header_tag["id"] = f'{self.title_id}{count}'
                    count += 1

                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = None
                        chap_num = None
                        sub_tag = None


                        chap_num = re.search(r'^((ARTICLE|Article)\s*(?P<ar>[A-Z]+|[I,V,X]+))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = re.search(r'^[a-zA-Z]{2}', header_tag.text.strip()).group()
                        sub_tag = f'-{sub_tag.lower()}-'
                        class_name = f'{chap_num.lower()}h2'
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["art_head"]]:
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(),re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    if re.search(r'^(ARTICLE)', header_tag.text.strip()):
                        tag_name = "h2"

                        prev_id = header_tag.find_previous("h2", class_='amendmenth2').get("id")
                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>[I,V,X]+))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^Section\s*[0-9]+(\.\d+)*[a-z]*\.', header_tag.text.strip()):
                        chap_num = re.search(r'^Section\s*(?P<ar>[0-9]+(\.\d+)*[a-z]*)\.', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2").get("id")

                        sub_tag = "-s"
                        class_name = "section"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["amd"]]:
                    if re.search(r'^AMENDMENTS', header_tag.text.strip(),re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h1").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-am-"
                        class_name = "amendmenth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.get("class") == [self.class_regex["head4"]]:

                    # if re.search(r'^[I,V,X]+\.|^[A-Z]\.', header_tag.text.strip()):
                    #     tag_name = "h5"
                    #
                    #     prev_id = header_tag.find_previous("h4").get("id")
                    #     chap_num = re.sub(r'[\s.]+', '', header_tag.text.strip()).lower()
                    #     sub_tag = "-"
                    #     class_name = "analysis"



                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[I,V,X]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[A-HJ-UW-Z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[I,V,X]+\.',
                                                                         tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                        # self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                        #                                      class_name)

                    else:
                        tag_name = "h4"
                        prev_id = header_tag.find_previous("h3").get("id")
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-"
                        class_name = "annotation"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                elif header_tag.name == "h3":
                    prev_id = header_tag.find_previous("h2").get("id")
                    cur_id = re.search(r'^§\s*(?P<id>\d+)\.', header_tag.text.strip()).group("id")
                    header_tag["id"] = f'{prev_id}{cur_id}'

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    header_tag.name = "li"

            # titles
            else:
                prev_tag = self.soup.find(class_=self.class_regex["ul"])
                prev_id1 = prev_tag.find_previous(
                        lambda tag: tag.name in ['p'] and re.search(r'^\w+',
                                                                    tag.text.strip()))
                if prev_id1:
                    if not re.search(r'^Cross references', prev_id1.text.strip()):
                        self.class_regex['nav_head'] = prev_id1['class']

                    else:
                        self.class_regex['nav_head'] = None


                if header_tag.get("class") == [self.class_regex["title"]]:
                    if re.search(r'^TITLE\s(?P<title_id>\d+)', header_tag.text.strip()):
                        self.title_id = re.search(r'^TITLE\s(?P<title_id>\d+)', header_tag.text.strip()).group(
                            'title_id').zfill(2)
                        header_tag.name = "h1"
                        header_tag.attrs = {}
                        header_tag["id"] = f't{self.title_id}'

                    if re.search(r'^SUBPART\s*(?P<id>\d+)',header_tag.text.strip()):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="parth2").get("id")
                        chap_num = re.search(r'^SUBPART\s*(?P<id>\d+)', header_tag.text.strip()).group(
                            "id").zfill(2)
                        sub_tag = "-sp"
                        class_name = "subparth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)


                elif header_tag.get("class") == [self.class_regex["head2"]]:
                    if re.search(r'^ARTICLE', header_tag.text.strip(), re.I):
                        tag_name = "h2"

                        if header_tag.find_previous("h2", class_="gnrlh2"):
                            prev_id = header_tag.find_previous("h2", class_="gnrlh2").get("id")
                        else:
                            prev_id = None

                        chap_num = re.search(r'^(ARTICLE\s*(?P<ar>\d+(\.\d+)*))', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-ar"
                        class_name = "articleh2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    elif re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip(), re.I):
                        tag_name = "h2"
                        prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")


                        chap_num = re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                            "ar").zfill(2)
                        sub_tag = "-p"
                        class_name = "parth2"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)

                    else:
                        tag_name = "h2"
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                        sub_tag = "-"
                        class_name = "gnrlh2"
                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)


                elif header_tag.get("class") == [self.class_regex["part_head"]] or header_tag.get("class") == self.class_regex["nav_head"] :
                    if re.search(r'\w+', header_tag.text.strip()):
                        header_tag["class"] = "nav_head"



                # elif header_tag.get("class") == self.class_regex["nav_head"]:
                #     if re.search(r'\w+', header_tag.text.strip()):
                #         header_tag["class"] = "nav_head"
                #
                # elif header_tag.get("class") == [self.class_regex["part_head"]]:
                #     if re.search(r'^PART', header_tag.text.strip(), re.I):
                #         tag_name = "h2"
                #         prev_id = header_tag.find_previous("h2", class_="articleh2").get("id")
                #         chap_num = re.search(r'^PART\s*(?P<ar>\d+)', header_tag.text.strip()).group(
                #             "ar").zfill(2)
                #         sub_tag = "-p"
                #         class_name = "parth2"
                #
                #         self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                #                                              class_name)



                elif header_tag.get("class") == [self.class_regex["sec_head"]]:
                    if re.search(r'^\d+(\.\d+)*-\d+(\.\d+)*-\d+\.*', header_tag.text.strip(), re.I):
                        tag_name = "h3"
                        prev_id = header_tag.find_previous("h2").get("id")

                        chap_num = re.search(r'^(?P<sid>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', header_tag.text.strip()).group(
                            "sid").zfill(2)
                        sub_tag = "-s"
                        class_name = "section"

                        self.set_appropriate_tag_name_and_id(tag_name, header_tag, chap_num, prev_id, sub_tag,
                                                             class_name)



                elif header_tag.get("class") == [self.class_regex["head4"]]:
                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous("h4").get("id")
                        chap_num = re.search(r'^(?P<id>[I,V,X]+)\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[A-HJ-UW-Z]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[I,V,X]+\.',
                                                                         tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', header_tag.text.strip()):
                        header_tag.name = "h5"
                        prev_id = header_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                        chap_num = re.search(r'^(?P<id>[0-9])\.', header_tag.text.strip()).group("id")
                        header_tag["id"] = f'{prev_id}-{chap_num}'

                    else:
                        header_tag.name = "h4"
                        if header_tag.find_previous("h3"):
                            prev_id = header_tag.find_previous("h3").get("id")
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            header_tag["id"] = f'{prev_id}-{chap_num}'
                        else:
                            chap_num = re.sub(r'[\s]+', '', header_tag.text.strip()).lower()
                            header_tag["id"] = f't{self.title_id}-{chap_num}'

                elif header_tag.get("class") == [self.class_regex["ul"]]:
                    if not re.search(r'^Section', header_tag.text.strip()):
                        header_tag.name = "li"


                elif header_tag.get("class") == [self.class_regex["Analysis"]]:
                    if re.search(r'^[I,V,X]+\.', header_tag.text.strip()):
                        if re.search(r'^I\.', header_tag.text.strip()):
                            header_tag.name = "ul"
                            header_tag["class"] = "leaders"
                            list1 = header_tag.text.splitlines()
                            header_tag.string = ""

                            for i in list1:
                                new_ul_tag = self.soup.new_tag("li")
                                new_ul_tag.string = i
                                header_tag.append(new_ul_tag)

    def recreate_tag(self):
        ol_list = []
        num_ol_tag = self.soup.new_tag("ol")
        ol_count = 1
        for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
            current_p_tag = p_tag.text.strip()

            next_sibling = p_tag.find_next_sibling()

            if re.search('^§', current_p_tag):
                if re.search('^§', p_tag.find_next("b").text.strip()):
                    p_tag.name = "div"
                    p_tag_text = str(p_tag)
                    h3_text = re.search(r'<b>(?P<sec_head>.+)</b>', p_tag_text).group("sec_head")
                    h3_tag = "<h3>" + h3_text + "</h3>"
                    p_text = re.sub(r'^<ol class="p4"><b>(.+)</b>|</ol>$', '', p_tag_text)
                    p_text = "<p class='p4'>" + p_text + "</p>"
                    p_tag.string = h3_tag + p_text
                    p_tag.name = "p"
                    p_tag.unwrap()

                else:
                    p_tag.name = "div"
                    p_tag_text = str(p_tag)
                    h3_text = re.search(r'<b>(?P<sec_head>.+)</b>', p_tag_text).group("sec_head")
                    h3_tag = "<h3> § " + h3_text + "</h3>"
                    p_text = re.sub(r'^<ol class="p4">§ <b>(.+)</b>|</ol>$', '', p_tag_text)
                    p_text = "<p class='p4'>" + p_text + "</p>"

                    if re.search(r'\s*\(1\)', p_text) and not re.search(r'^§\s*\(1\)', p_text):
                        p_text = "<li class='p4'>" + p_text + "</li>"
                        p_text = "<ol>" + p_text + "</ol>"
                        p_tag.string = h3_tag + p_text
                        p_tag.unwrap()

                    else:
                        p_tag.string = h3_tag + p_text

        print("tags are recreated")

    def recreate_tag1(self):
        ol_list = []
        num_ol_tag = self.soup.new_tag("ol")
        ol_count = 1
        ul_tag = self.soup.new_tag("ul")

        for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
            current_p_tag = p_tag.text.strip()

            next_sibling = p_tag.find_next_sibling()

            if re.search('^§', current_p_tag):
                if re.search('^§', p_tag.find_next("b").text.strip()):
                    p_tag.find_next("b").name = "h3"
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()

                else:
                    new_h3_tag = self.soup.new_tag("h3")
                    h3_text = "§" + p_tag.find_next("b").text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()

                    if re.search(r'^§', p_tag.text.strip()):
                        p_tag.string = re.sub(r'^§', '', p_tag.text.strip())



            if re.search(r'^\(\d+\)',current_p_tag):
               if p_tag.find_next().name == "b":
                    alpha_text = re.sub(r'^[^.]+\.','',current_p_tag)
                    num_text = re.sub(r'\(a\).+','',current_p_tag)

                    if re.search(r'^\s*\([a-z]\)',alpha_text):
                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = alpha_text
                        new_p_tag["class"] = [self.class_regex['ol']]
                        p_tag.insert_after(new_p_tag)
                        p_tag.string = num_text


        for anlys_tag in self.soup.find_all(class_=self.class_regex['Analysis']):
            if re.search(r'^I\.', anlys_tag.text.strip()):
                anlys_tag.name = "ul"
                anlys_tag["class"] = "leaders"
                list1 = anlys_tag.text.splitlines()
                anlys_tag.string = ""

                for i in list1:
                    new_ul_tag = self.soup.new_tag("li")
                    new_ul_tag.string = i

                    anlys_tag.append(new_ul_tag)

    def convert_roman_to_digit(self, roman):
        value = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}
        prev = 0
        ans = 0
        length = len(roman)
        for num in range(length - 1, -1, -1):
            if value[roman[num]] >= prev:
                ans += value[roman[num]]
            else:
                ans -= value[roman[num]]
            prev = value[roman[num]]

        return ans

    def create_and_wrap_with_ol_tag(self):
        ol_list = []
        ol_count = 1
        num_ol_tag = self.soup.new_tag("ol")
        prev_head_id = None
        innr_alpha_ol_tag = self.soup.new_tag("ol", type="A", **{"class": "alpha"})

        for p_tag in self.soup.find_all(class_=self.class_regex['ol']):
            current_li_tag = p_tag.text.strip()

            # (1)
            if re.search(r'^\(\d+\)', current_li_tag):
                p_tag.name = "li"
                num_curr_tag = p_tag

                if re.search(r'^\(1\)', current_li_tag):

                    if re.match(r'^ARTICLE', p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "br":
                        prev_head_id = p_tag.find_previous("h2").get("id")
                    else:
                        prev_head_id = p_tag.find_previous("h3").get("id")

                    num_ol_tag = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol_tag)

                    if prev_head_id in ol_list:
                        ol_count += 1
                    else:
                        ol_count = 1

                    ol_list.append(prev_head_id)
                    p_tag["id"] = f'{prev_head_id}ol{ol_count}1'

                else:

                    if re.search(r'^\((\d+)(\.\d+)*\)(\s*\(\w\))*', p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
                            cur_tag = re.search(r'^\((?P<cid>\d+)\)', current_li_tag).group("cid")
                            prev_tag = re.search(r'^\((?P<pid>\d+)(\.\d+)*\)(\s*\(\w\))*',
                                                 p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
                                "pid")

                            if int(cur_tag) == (int(prev_tag)) + 1:
                                num_ol_tag.append(p_tag)

                            p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}'

                    elif re.search(r'^\(\D\)|^\([I,V,X]+\)',
                                   p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):

                            cur_tag = re.search(r'^\((?P<cid>\d+)\)', current_li_tag).group("cid")
                            prev_tag = re.search(r'^\((?P<pid>\d+)\)', p_tag.find_previous(
                                lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
                                                                             tag.text.strip())).text.strip()).group("pid")

                            if int(cur_tag) == (int(prev_tag)) + 1:
                                num_ol_tag.append(p_tag)

                            p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag}'




                if re.search(r'^\(\d+\)\s\(\D\)', current_li_tag):
                    alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_li_tag)

                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>\D)\)', current_li_tag)
                    prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    alpha_ol_tag.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol_tag)

                    if re.search(r'^\(\d+\)\s*\(\D\)\s*\d\.', current_li_tag):
                        innr_num_ol_tag = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.append(current_li_tag)

                        cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\D)\)\s*(?P<id2>\d)\.', current_li_tag)
                        innr_num_ol_tag[
                            "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                        innr_num_ol_tag.append(inner_li_tag)
                        p_tag.insert(1, innr_num_ol_tag)
                        innr_num_ol_tag.find_previous().string.replace_with(innr_num_ol_tag)


            # (2.5)
            elif re.search(r'^\(\d+\.\d+\)', current_li_tag):
                p_tag.name = "p"
                prev_tag = p_tag.find_previous(
                    lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
                                                                 tag.text.strip()))
                prev_id  = re.search(r'^\((?P<pid>\d+)\)', p_tag.find_previous(
                    lambda tag: tag.name in ['li'] and re.search(r'^\(\d+\)',
                                                                 tag.text.strip())).text.strip()).group("pid")
                cur_tag = re.search(r'^\((?P<cid1>(?P<cid>\d+)\.\d+)\)', current_li_tag)

                p_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid1")}'

                if cur_tag.group("cid") == prev_id:
                    prev_tag.append(p_tag)


                if re.search(r'^\(\d+\.\d+\)\s*\(\w\)', current_li_tag):

                    # print(current_li_tag)

                    alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_li_tag)

                    cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)\s*\((?P<pid>\w)\)', current_li_tag)
                    prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    alpha_ol_tag.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol_tag)


            # (a)
            elif re.search(r'^\(\s*[a-z]\s*\)', current_li_tag):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                if re.search(r'^\(a\)', current_li_tag):

                    alpha_ol_tag = self.soup.new_tag("ol", type="a", **{"class": "alpha"})

                    if re.search(r'^\(\d+\)',
                                 p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span" or p_tag.find_previous().name == "b":
                        prev_tag1 = p_tag.find_previous("li")
                        p_tag.wrap(alpha_ol_tag)

                        prev_tag1.append(alpha_ol_tag)
                        prev_tag_id = f'{prev_tag1.get("id")}ol{ol_count}'
                        p_tag["id"] = f'{num_curr_tag.get("id")}a'
                    else:
                        p_tag.wrap(alpha_ol_tag)

                else:

                    if re.search(r'^\([I,V,X]+\)|^\(\d+\)\s\(\D\)',
                                 p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
                        cur_tag = re.search(r'\(\s*(?P<cid>[a-z])\s*\)', current_li_tag).group("cid")
                        prev_tag = re.search(r'^(\(\d+(\.\d+)*\))*\s*\((?P<pid>[a-z])\s*\)',
                                             p_tag.find_previous(
                                                 lambda tag: tag.name in ['li','p'] and re.search(
                                                     r'^(\(\d+\))*\s*\((?P<pid>[a-z])\s*\)|^\(\d+\.\d+\)\s*\(\w\)',
                                                     tag.text.strip())).text.strip()).group(
                            "pid")


                        if ord(cur_tag) == (ord(prev_tag)) + 1:
                            alpha_ol_tag.append(p_tag)

                        p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'



                    elif re.search(r'^\(\s*[a-z]\s*\)',
                                   p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
                        cur_tag = re.search(r'\(\s*(?P<cid>[a-z]+)\s*\)', current_li_tag).group("cid")
                        prev_tag = re.search(r'\(\s*(?P<pid>[a-z]+)\s*\)',
                                             p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
                            "pid")

                        if ord(cur_tag) == (ord(prev_tag)) + 1:
                            alpha_ol_tag.append(p_tag)
                            p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'

                        elif ord(cur_tag) == (ord(prev_tag)):
                            alpha_ol_tag.append(p_tag)
                            cur_tag = chr(ord(cur_tag) + 1)
                            p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'

                        elif ord(cur_tag) == (ord(prev_tag)) + 2:
                            alpha_ol_tag.append(p_tag)
                            p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'

                    # else:
                    #     print(p_tag)
                    #     print(p_tag.find_previous(class_=self.class_regex['ol']))




                if re.search(r'^\(\w+\)\s*\([I,V,X]+\)', current_li_tag):
                    rom_ol_tag = self.soup.new_tag("ol",type="I", **{"class": "roman"})
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_li_tag)

                    cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_li_tag)
                    prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    rom_ol_tag.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(rom_ol_tag)


            # (I)
            elif re.search(r'^\([I,V,X]+\)', current_li_tag):
                p_tag.name = "li"

                if re.search(r'^\(I\)', current_li_tag):
                    rom_ol_tag = self.soup.new_tag("ol",type="I", **{"class": "roman"})

                    if re.search(r'^\(\d+\)\s\(\D\)|^\(\w\)|^\(\d+\.\d+\)\s*\(\w\)',
                                 p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span":
                        prev_tag1 = p_tag.find_previous("li")
                        p_tag.wrap(rom_ol_tag)
                        prev_tag1.append(rom_ol_tag)
                        prev_tag_id = f'{prev_tag1.get("id")}ol{ol_count}'
                        p_tag["id"] = f'{prev_tag1.get("id")}I'
                    else:
                        p_tag.wrap(rom_ol_tag)

                else:

                    if re.search(r'^\([I,V,X]+\)', p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
                        cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
                        prev_id = re.search(r'^\((?P<pid>[I,V,X]+)\)',
                                            p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
                            "pid")

                        if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
                            rom_ol_tag.append(p_tag)

                            p_tag["id"] = f'{prev_tag1.get("id")}{cur_id}'


                    elif re.search(r'^\(\w+\)\s*\([I,V,X]+\)|^\(\s*[A-Z]\s*\)',
                                   p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):


                        cur_id = re.search(r'^\((?P<cid>[I,V,X]+)\)', current_li_tag).group("cid")
                        prev_tag =p_tag.find_previous(lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)',
                                                                         tag.text.strip()))

                        prev_id = re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)', p_tag.find_previous(
                            lambda tag: tag.name in ['li'] and re.search(r'^\(\w+\)\s*\((?P<pid>[I,V,X]+)\)',
                                                                         tag.text.strip())).text.strip()).group("pid")

                        if self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 1:
                            rom_ol_tag.append(p_tag)
                            p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'

                            # p_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_id}'

                        elif self.convert_roman_to_digit(cur_id) == self.convert_roman_to_digit(prev_id) + 2:
                            rom_ol_tag.append(p_tag)
                            p_tag["id"] = f'{prev_tag.get("id")}{cur_id}'





                if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)', current_li_tag):
                    innr_alpha_ol_tag = self.soup.new_tag("ol", type="A",**{"class": "roman"})
                    li_tag = self.soup.new_tag("li")
                    li_tag.append(current_li_tag)

                    # cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>[I,V,X]+)\)', current_li_tag)
                    # prev_tag_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    # li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    innr_alpha_ol_tag.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(innr_alpha_ol_tag)



        #(A)

            elif re.search(r'^\(\s*[A-Z]\s*\)', current_li_tag):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                if re.search(r'^\(A\)', current_li_tag):
                    innr_alpha_ol_tag = self.soup.new_tag("ol", type="A", **{"class": "alpha"})

                    if re.search(r'^\([I,V,X]+\)',
                                 p_tag.find_previous().text.strip()) or p_tag.find_previous().name == "span" or p_tag.find_previous().name == "b":
                        prev_id = p_tag.find_previous()
                        p_tag.wrap(innr_alpha_ol_tag)

                        rom_ol_tag.append(innr_alpha_ol_tag)
                        prev_tag_id = f'{prev_id.get("id")}ol{ol_count}'
                        p_tag["id"] = f'{num_curr_tag.get("id")}A'
                    else:
                        p_tag.wrap(innr_alpha_ol_tag)


                else:

                    if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)',
                                 p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):

                        # print(current_li_tag)

                        cur_tag = re.search(r'^\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
                        prev_id = re.search(r'^\([I,V,X]+\)\s*\((?P<pid>[A-Z])\)', p_tag.find_previous(
                            lambda tag: tag.name in ['li'] and re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)',
                                                                         tag.text.strip())).text.strip()).group("pid")

                        if ord(cur_tag) == (ord(prev_id)) + 1:
                            innr_alpha_ol_tag.append(p_tag)
                            p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'

                    elif re.search(r'^\(\s*[A-Z]\s*\)',
                                   p_tag.find_previous(class_=self.class_regex['ol']).text.strip()):
                        cur_tag = re.search(r'\(\s*(?P<cid>[A-Z]+)\s*\)', current_li_tag).group("cid")
                        prev_id = re.search(r'\(\s*(?P<pid>[A-Z]+)\s*\)',
                                             p_tag.find_previous(class_=self.class_regex['ol']).text.strip()).group(
                            "pid")

                        if ord(cur_tag) == (ord(prev_id)) + 1:
                            innr_alpha_ol_tag.append(p_tag)
                            p_tag["id"] = f'{num_curr_tag.get("id")}{cur_tag}'





        print("ol tag created")

    def create_ul_tag(self):

        if re.search('constitution', self.html_file_name):
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            nav_tag = self.soup.new_tag("nav")
            for list_item in self.soup.find_all(class_=self.class_regex['ul']):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)
                    ul_tag.wrap(self.soup.new_tag("nav"))
        else:
            ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            for list_item in self.soup.find_all("li"):
                if list_item.find_previous().name == "li":
                    ul_tag.append(list_item)
                else:
                    ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    list_item.wrap(ul_tag)

                    if ul_tag.find_previous().find_previous().name == "h1":
                        ul_tag.find_previous("nav").append(ul_tag)
                    else:
                        ul_tag.wrap(self.soup.new_tag("nav"))

        print("ul tag is created")

    def set_chapter_section_nav(self, list_item, chap_num, sub_tag, prev_id, sec_num):
        nav_list = []
        nav_link = self.soup.new_tag('a')
        nav_link.append(list_item.text)

        if re.search('constitution', self.html_file_name):
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                title_id = list_item.find_previous("h1").get("id")
                nav_link["href"] = f"#{title_id}{sub_tag}{chap_num}"
        else:
            if prev_id:
                nav_link["href"] = f"#{prev_id}{sub_tag}{chap_num}"
            else:
                nav_link["href"] = f"#t{self.title_id}-{sub_tag}{chap_num}"

        nav_list.append(nav_link)
        list_item.contents = nav_list

    def create_chapter_section_nav(self):
        count = 0
        for list_item in self.soup.find_all(class_=self.class_regex['ul']):
            if re.search('constitution', self.html_file_name):
                if re.match(r'^ARTICLE', list_item.text.strip()):
                    chap_num = re.search(r'^ARTICLE\s*(?P<ar>[A-Z]+)',
                                         list_item.text.strip()).group(
                        "ar").zfill(2)
                    sub_tag = "-ar"
                    prev_id = None

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                elif re.search(r'^[I,V,X]+\.', list_item.text.strip()):
                    prev_id = list_item.find_previous("h2").get("id")
                    chap_num = re.search(r'^(?P<ar>[I,V,X]+)\.', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-ar"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.search(r'^[I,V,X]+', list_item.text.strip()):
                    prev_id = None
                    chap_num = re.search(r'^(?P<ar>[I,V,X]+)', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-ar"
                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.search(r'[0-9a-z]+\.', list_item.text.strip()):
                    prev_id = list_item.find_previous("h2").get("id")
                    chap_num = re.search(r'^(?P<ar>[0-9a-z]+)\.', list_item.text.strip()).group("ar").zfill(2)
                    sub_tag = "-s"

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)

                else:
                    if not re.search(r'^Section|^Article', list_item.text.strip()):
                        prev_id = None
                        chap_num = re.sub(r'[\s]+', '', list_item.text.strip()).lower()
                        sub_tag = re.search(r'^[a-zA-Z]{2}', list_item.text.strip()).group()
                        sub_tag = f'-{sub_tag.lower()}-'

                        self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


            #title
            else:
                if re.match(r'^Art\.\s*\d+\.', list_item.text.strip()):
                    chap_num = re.search(r'^Art\.\s*(?P<id>\d+(\.\d+)*)\.',
                                         list_item.text.strip()).group(
                        "id").zfill(2)

                    if list_item.find_previous("p", class_="nav_head"):
                        sub_tag = "-ar"
                        prev_id1 = re.sub(r'[\s]+', '', list_item.find_previous("p", class_="nav_head").text.strip()).lower()
                        prev_id = f't{self.title_id}-{prev_id1}'
                    else:
                        sub_tag = "ar"
                        prev_id = None

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


                elif re.match(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', list_item.text.strip()):
                    chap_num = re.search(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+)\.*', list_item.text.strip()).group("id").zfill(
                        2)

                    if re.match(r'^Section', list_item.find_previous("p").text.strip()):
                        prev_id = list_item.find_previous("h2", class_="articleh2").get("id")
                    else:
                        # prev_id1 = list_item.find_previous("h2", class_="articleh2").get("id")

                        if re.search(r'^PART\s*(?P<id>\d+)',list_item.find_previous("p", class_="nav_head").text.strip()):
                            prev_id1 = list_item.find_previous("h2", class_="articleh2").get("id")
                            prev_id2 = re.search(r'^PART\s*(?P<id>\d+)',
                                                 list_item.find_previous("p", class_="nav_head").text.strip()).group(
                                "id").zfill(2)
                            prev_id = f"{prev_id1}-p{prev_id2}"
                            prev_id4 = f"{prev_id1}-p{int(prev_id2)+1:02}"

                        elif re.search(r'^SUBPART\s*(?P<id>\d+)',list_item.find_previous("p", class_="nav_head").text.strip()):
                            prev_id1 = prev_id4
                            prev_id2 = re.search(r'^SUBPART\s*(?P<id>\d+)',
                                                 list_item.find_previous("p", class_="nav_head").text.strip()).group(
                                "id").zfill(2)
                            prev_id = f"{prev_id1}-sp{prev_id2}"
                        else:
                            prev_id = list_item.find_previous("h2", class_="parth2").get("id")

                    sub_tag = "-s"

                    self.set_chapter_section_nav(list_item, chap_num, sub_tag, prev_id, None)


        ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})

        for li_tag in self.soup.find_all("li"):
            if not li_tag.get('class'):
                if re.search('constitution', self.html_file_name):
                    # prev_id = li_tag.find_previous("h4").get("id")
                    # chap_num = re.sub(r'[\s.]+', '', li_tag.text.strip()).lower()
                    # sub_tag = "-"
                    # self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)



                    if re.search(r'^[A-HJ-UW-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(ul_analy_tag)
                            prev_li.append(ul_analy_tag)

                            if li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                            tag.text.strip())):
                                prev_id1 = re.sub(r'^#','',li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())).get("href"))
                            else:
                                prev_id1 = None

                            chap_num = "A"
                        else:
                            chap_num = re.search(r'^(?P<id>[A-HJ-UW-Z])\.', li_tag.text.strip()).group("id")
                            ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id1, None)

                    elif re.search(r'^[1-9]\.', li_tag.text.strip()):
                        if re.search(r'^1\.', li_tag.text.strip()):
                            num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(num_ul_analy_tag)
                            prev_li.append(num_ul_analy_tag)
                            prev_id2 = re.sub(r'^#', '', li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[A-Z]+\.',
                                                                            tag.text.strip())).get("href"))
                            chap_num = "1"

                        else:
                            chap_num = re.search(r'^(?P<id>[1-9])\.', li_tag.text.strip()).group("id")
                            num_ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id2, None)

                    if re.search(r'^[I,V,X]+\.',li_tag.text.strip()):
                        if re.search(r'^I\.',li_tag.text.strip()) and re.search(r'^H\.',li_tag.find_previous("li").text.strip()):
                            ul_analy_tag.append(li_tag)
                            prev_id3 = prev_id1

                        elif re.search(r'^I\.',li_tag.text.strip()):
                            prev_id3 = li_tag.find_previous("h4").get("id")

                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)',li_tag.text.strip()).group("ar")
                        prev_id = prev_id3
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)




                else:
                    if re.search(r'^[A-HJ-UW-Z]\.', li_tag.text.strip()):
                        if re.search(r'^A\.', li_tag.text.strip()):
                            ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(ul_analy_tag)
                            prev_li.append(ul_analy_tag)

                            if li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                            tag.text.strip())):
                                prev_id1 = re.sub(r'^#','',li_tag.find_previous(
                                    lambda tag: tag.name in ['a'] and re.search(r'^[I,V,X]+\.',
                                                                                tag.text.strip())).get("href"))
                            else:
                                prev_id1 = None

                            chap_num = "A"
                        else:
                            chap_num = re.search(r'^(?P<id>[A-HJ-UW-Z])\.', li_tag.text.strip()).group("id")
                            ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id1, None)

                    elif re.search(r'^[1-9]\.', li_tag.text.strip()):
                        if re.search(r'^1\.', li_tag.text.strip()):
                            num_ul_analy_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            prev_li = li_tag.find_previous("li")
                            li_tag.wrap(num_ul_analy_tag)
                            prev_li.append(num_ul_analy_tag)
                            prev_id2 = re.sub(r'^#', '', li_tag.find_previous(
                                lambda tag: tag.name in ['a'] and re.search(r'^[A-Z]+\.',
                                                                            tag.text.strip())).get("href"))
                            chap_num = "1"

                        else:
                            chap_num = re.search(r'^(?P<id>[1-9])\.', li_tag.text.strip()).group("id")
                            num_ul_analy_tag.append(li_tag)
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id2, None)

                    if re.search(r'^[I,V,X]+\.',li_tag.text.strip()):
                        if re.search(r'^I\.',li_tag.text.strip()) and re.search(r'^H\.',li_tag.find_previous("li").text.strip()):
                            ul_analy_tag.append(li_tag)
                            prev_id3 = prev_id1

                        elif re.search(r'^I\.',li_tag.text.strip()):
                            prev_id3 = li_tag.find_previous("h4").get("id")

                        chap_num = re.search(r'^(?P<ar>[I,V,X]+)',li_tag.text.strip()).group("ar")
                        prev_id = prev_id3
                        sub_tag = "-"
                        self.set_chapter_section_nav(li_tag, chap_num, sub_tag, prev_id, None)




    def write_soup_to_file(self):

        """
            - add the space before self closing meta tags
            - convert html to str
            - write html str to an output file
        """

        soup_str = str(self.soup.prettify(formatter=None))
        with open(f"/home/mis/cic-code-co/transforms/co/occo/r{self.release_number}/{self.html_file_name}",
                  "w") as file:
            file.write(soup_str)

    # add css file
    def css_file(self):
        head = self.soup.find("head")
        style = self.soup.head.find("style")
        style.decompose()
        css_link = self.soup.new_tag("link")
        css_link.attrs[
            "href"] = "https://unicourt.github.io/cic-code-ga/transforms/ga/stylesheet/ga_code_stylesheet.css"
        css_link.attrs["rel"] = "stylesheet"
        css_link.attrs["type"] = "text/css"
        head.append(css_link)

    def start_parse(self):

        """
                     - set the values to instance variables
                     - check if the file is constitution file or title file
                     - based on file passed call the methods to parse the passed htmls
        """

        self.release_label = f'Release-{self.release_number}'
        print(self.html_file_name)
        start_time = datetime.now()
        print(start_time)
        self.create_page_soup()
        self.css_file()

        if re.search('constitution', self.html_file_name):
            self.class_regex = {'ul': '^(§ )|^(ARTICLE)', 'head2': '^(§ )|^(ARTICLE)',
                                'title': '^Declaration of Independence|^Constitution of the State of Colorado|^COLORADO COURT RULES',
                                'sec_head': r'^Section\s*[0-9a-z]+\.',
                                'junk': '^Statute text', 'ol': r'^(\(1\))',
                                'head4': '^ANNOTATIONS', 'art_head': '^ARTICLE',
                                'amd': '^AMENDMENTS', 'Analysis': '^I\.'}

            self.get_class_name()
            self.remove_junk()
            self.recreate_tag1()
            self.replace_tags()
            self.create_ul_tag()
            self.create_chapter_section_nav()
            # self.create_and_wrap_with_ol_tag()



        #     self.create_and_wrap_with_div_tag()
        #     self.add_citation1()
        #     self.add_watermark_and_remove_class_name()


        else:
            self.get_class_name()
            self.remove_junk()
            self.replace_tags()
            self.create_ul_tag()

            self.create_chapter_section_nav()










        #     self.get_class_name()
        #     self.remove_junk()
        #     self.replace_tags()
        #     self.create_main_tag()
        #     self.create_ul_tag()
        #     self.create_chapter_section_nav()
        #     self.create_ref_link_to_notetodecision_nav()
        #     self.create_ul_tag_to_notes_to_decision()
        #     self.create_and_wrap_with_div_tag()
        #     self.wrap_with_ordered_tag()
        #     self.create_numberical_ol()
        #     self.add_citation1()
        #     self.add_watermark_and_remove_class_name()

        self.write_soup_to_file()
        print(datetime.now() - start_time)

# --input_file_name gov.co.crs.title.01.html