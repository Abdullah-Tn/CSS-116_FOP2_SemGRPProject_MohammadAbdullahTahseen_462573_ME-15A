import feedparser
import string
import time
import threading
from project_util import translate_html
from mtTkinter import *
from datetime import datetime
import pytz

#-----------------------------------------------------------------------

#======================
# Code for retrieving and parsing
# Google and Yahoo News feeds
# Do not change this code
#======================

def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.get('guid', '')
        title = translate_html(entry.get('title', ''))
        link = entry.get('link', '')
        description = translate_html(entry.get('description', '')) if 'description' in entry else ''
        pubdate = translate_html(entry.get('published', ''))

        # Try parsing the date with different formats
        pubdate_parsed = None
        date_formats = ["%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ"]

        for fmt in date_formats:
            try:
                pubdate_parsed = datetime.strptime(pubdate, fmt)
                pubdate_parsed = pubdate_parsed.replace(tzinfo=pytz.timezone("GMT"))
                break
            except ValueError:
                continue

        if pubdate_parsed is None:
            raise ValueError(f"Date format not recognized for: {pubdate}")

        newsStory = NewsStory(guid, title, description, link, pubdate_parsed)
        ret.append(newsStory)
    return ret

#======================
# Data structure design
#======================

# Problem 1

# TODO: NewsStory
class NewsStory:
    def __init__(self, guid, title, description, link, pubdate):
        self.guid = guid
        self.title = title
        self.description = description
        self.link = link
        self.pubdate = pubdate
    
    def get_guid(self):
        return self.guid
    
    def get_title(self):
        return self.title
    
    def get_description(self):
        return self.description
    
    def get_link(self):
        return self.link
    
    def get_pubdate(self):
        return self.pubdate

#======================
# Triggers
#======================

class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        # DO NOT CHANGE THIS!
        raise NotImplementedError

# PHRASE TRIGGERS
# Problem 2
# TODO: PhraseTrigger
class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase.lower()

    def is_phrase_in(self, text):
        text = text.lower()
        for punc in string.punctuation:
            text = text.replace(punc, ' ')
        words = text.split()
        normalized_text = ' '.join(words)
        return f' {self.phrase} ' in f' {normalized_text} '

    def evaluate(self, story):
        raise NotImplementedError  # This class is abstract, so it shouldn't implement evaluate directly

# Problem 3
# TODO: TitleTrigger
class TitleTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_title())

# Problem 4
# TODO: DescriptionTrigger
class DescriptionTrigger(PhraseTrigger):
    def evaluate(self, story):
        return self.is_phrase_in(story.get_description())

# TIME TRIGGERS

# Problem 5
# TODO: TimeTrigger
# Constructor:
#        Input: Time has to be in EST and in the format of "%d %b %Y %H:%M:%S".
#        Convert time from string to a datetime before saving it as an attribute.
class TimeTrigger(Trigger):
    def __init__(self, time_string):
        # Convert the time string to a datetime object in UTC
        self.time = datetime.strptime(time_string, "%d %b %Y %H:%M:%S")
        # Set the timezone to UTC
        self.time = self.time.replace(tzinfo=pytz.utc)
        # Convert to EST timezone
        self.time = self.time.astimezone(pytz.timezone("US/Eastern"))

# Problem 6
# TODO: BeforeTrigger and AfterTrigger
class BeforeTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate() < self.time

class AfterTrigger(TimeTrigger):
    def evaluate(self, story):
        return story.get_pubdate() > self.time

# COMPOSITE TRIGGERS

# Problem 7
# TODO: NotTrigger
class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self, story):
        return not self.trigger.evaluate(story)

# Problem 8
# TODO: AndTrigger
class AndTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) and self.trigger2.evaluate(story)

# Problem 9
# TODO: OrTrigger
class OrTrigger(Trigger):
    def __init__(self, trigger1, trigger2):
        self.trigger1 = trigger1
        self.trigger2 = trigger2

    def evaluate(self, story):
        return self.trigger1.evaluate(story) or self.trigger2.evaluate(story)

#======================
# Filtering
#======================

# Problem 10
def filter_stories(stories, triggerlist):
    """
    Takes in a list of NewsStory instances.

    Returns: a list of only the stories for which a trigger in triggerlist fires.
    """
    # TODO: Problem 10
    filtered_stories = []
    
    for story in stories:
        for trigger in triggerlist:
            if trigger.evaluate(story):
                filtered_stories.append(story)
                break  # No need to check other triggers if one has fired
                
    return filtered_stories

#======================
# User-Specified Triggers
#======================
# Problem 11
def read_trigger_config(triggers):
    """
    filename: the name of a trigger configuration file

    Returns: a list of trigger objects specified by the trigger configuration file.
    """
    try:
        trigger_file = open(triggers, 'r')
    except FileNotFoundError:
        print(f"Error: The file {triggers} was not found.")
        return []

    lines = []
    for line in trigger_file:
        line = line.rstrip()
        if not (len(line) == 0 or line.startswith('//')):
            lines.append(line)

    def parse_trigger_line(line):
        parts = line.split(',')
        trigger_name = parts[0].strip()
        trigger_type = parts[1].strip()
        trigger_args = [arg.strip() for arg in parts[2:]]
        return trigger_name, trigger_type, trigger_args

    triggers = {}
    trigger_list = []
    for line in lines:
        if line.startswith('ADD'):
            trigger_names = line.split(',')[1:]
            trigger_list.extend(triggers[name] for name in trigger_names if name in triggers)
        else:
            trigger_name, trigger_type, trigger_args = parse_trigger_line(line)
            if trigger_type == 'TITLE':
                trigger = TitleTrigger(*trigger_args)
            elif trigger_type == 'DESCRIPTION':
                trigger = DescriptionTrigger(*trigger_args)
            elif trigger_type == 'AFTER':
                trigger = AfterTrigger(*trigger_args)
            elif trigger_type == 'BEFORE':
                trigger = BeforeTrigger(*trigger_args)
            elif trigger_type == 'NOT':
                trigger = NotTrigger(triggers[trigger_args[0]])
            elif trigger_type == 'AND':
                trigger = AndTrigger(triggers[trigger_args[0]], triggers[trigger_args[1]])
            elif trigger_type == 'OR':
                trigger = OrTrigger(triggers[trigger_args[0]], triggers[trigger_args[1]])
            triggers[trigger_name] = trigger

    return trigger_list

SLEEPTIME = 120  # seconds -- how often we poll

def main_thread(master):
    try:
        # HELPER CODE - you don't need to understand this!
        # Draws the popup window that displays the filtered stories
        # Retrieves and filters the stories from the RSS feeds
        frame = Frame(master)
        frame.pack(side=BOTTOM)
        scrollbar = Scrollbar(master)
        scrollbar.pack(side=RIGHT, fill=Y)

        t = "Google & Yahoo Top News"
        title = StringVar()
        title.set(t)
        ttl = Label(master, textvariable=title, font=("Helvetica", 18))
        ttl.pack(side=TOP)
        cont = Text(master, font=("Helvetica", 14), yscrollcommand=scrollbar.set)
        cont.pack(side=BOTTOM)
        cont.tag_config("title", justify='center')
        button = Button(frame, text="Exit", command=root.destroy)
        button.pack(side=BOTTOM)
        guidShown = []

        def get_cont(newstory):
            if newstory.get_guid() not in guidShown:
                cont.insert(END, newstory.get_title() + "\n", "title")
                cont.insert(END, "\n---------------------------------------------------------------\n", "title")
                cont.insert(END, newstory.get_description())
                cont.insert(END, "\n*************************\n", "title")
                guidShown.append(newstory.get_guid())

        while True:
            print("Polling . . .", end=' ')
            # Get stories from Google's Top Stories RSS news feed
            stories = process("http://news.google.com/news?output=rss")

            # Get stories from Yahoo's Top Stories RSS news feed
            stories.extend(process("http://news.yahoo.com/rss/topstories"))

            # Problem 11
            triggerlist = read_trigger_config('triggers.txt')

            stories = filter_stories(stories, triggerlist)

            list(map(get_cont, stories))
            scrollbar.config(command=cont.yview)

            print("Sleeping...")
            time.sleep(SLEEPTIME)

    except Exception as e:
        print(e)

if __name__ == '__main__':
    root = Tk()
    root.title("Some RSS parser")
    t = threading.Thread(target=main_thread, args=(root,))
    t.start()
    root.mainloop()