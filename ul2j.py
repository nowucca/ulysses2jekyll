"""
Usage: ul2j in-folder out-jekyll-folder

Assumes an index.md and images/ folder is given as input.
All image names will be preserved as specified.

A title will be derived from the file.
A post will then be added to the jekyll folder posts directory prefixed with today's date.
"""
import sys
import os
import shutil
import re
import datetime


def main():
    ulysses_export_folder = sys.argv[1]
    jekyll_folder = sys.argv[2]

    try:
        (title, file_title) = derive_title(ulysses_export_folder)
        if title is not None:
            now = datetime.datetime.now(tz=None)
            now = now.astimezone(datetime.timezone(datetime.timedelta(hours=-8), 'PST'))
            date_string = now.strftime("%Y-%m-%d")
            input_post_file = ulysses_export_folder + '/index.md'
            output_post_file = jekyll_folder + "/_posts/" + date_string + "-" + file_title + ".markdown"
            print("Transforming post:\n\t%s to\n\t%s\n\n" % (input_post_file, output_post_file))
            copy_images(ulysses_export_folder, jekyll_folder)
            with open(output_post_file, "w") as post:
                post.write("\n".join(["---",
                                      "layout: post",
                                      "title: "+title,
                                      "date: "+now.strftime("%Y-%m-%d %H:%M:%S %z"),
                                      "comments: true",
                                      "---\n\n"]))
                with open(input_post_file) as source:
                    lines = [line.rstrip() for line in source]
                    lines = [use_kramdown_image_tag(line) for line in lines]
                    post.write("\n".join(lines))
    except Exception as e:
        print("Encountered error ", e)


def get_valid_filename(s):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().lower().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def derive_title(folder):
    with open(folder+'/index.md') as f:
        lines = [line.rstrip() for line in f]
        for li in lines:
            if li.startswith('# '):
                raw_title = li[2:]
                file_title = get_valid_filename(raw_title)
                return raw_title, file_title
    return None, None

def is_image_file(entry):
    result = False

    extensions = [ '.jpg', '.png' ]
    for ext in extensions:
        upperExt = ext.upper()
        filename = str(entry.name)
        if filename.endswith(ext) or filename.endswith(upperExt):
            result = True
            break

    return result

def copy_images(ulysses_folder, jekyll_folder):
    src = ulysses_folder
    dest = jekyll_folder + "/images"

    try:
        with os.scandir(src) as entries:
            for entry in entries:
                if entry.is_file() and is_image_file(entry):
                    src_image = src + '/' + entry.name
                    dest_image = dest + "/" + entry.name
                    print("Copying %s -> %s" % (src_image, dest_image))
                    shutil.copy2(src_image, dest_image)
    except Exception as e:
        print('Exception copying images: ', e)


def use_kramdown_image_tag(line):
    """
    Take regular markdown image references and convert them to kramdown image tags.
    Handles multiple image references on each line.

    Detect a pattern line like

    ![](/images/headshot.jpg "Nowucca" width=200 height=200)

    and transform it to

    ![](/images/headshot.jpg "Nowucca"){: width="200" height="200"}
    """
    line_regex = r'!\[(.*)\]\(([^\ ]+)\ (".*")?(.*)\)'
    line_match = re.search(line_regex, line)
    if line_match:
        title = line_match.group(1)
        path = line_match.group(2)
        caption = line_match.group(3)
        block_attributes = line_match.group(4)
        if block_attributes:
            block_attributes = block_attributes.strip(' ')
            block_attributes = block_attributes.replace('=', '=\"')
            block_attributes = block_attributes.replace(' ', '\" ')
            block_attributes += "\""

        image = "![%s](%s %s)%s" % (title, '/images/'+path,
                                    caption if caption is not None else "",
                                    "{: "+block_attributes+" }" if block_attributes else "")

        line = line[0:line_match.start()] + image + use_kramdown_image_tag(line[line_match.end():])
    return line


if __name__ == "__main__":
    main()
    # kramdown_image_width_height("begin ![](/images/headshot.jpg width=200 height=200) end")
    # kramdown_image_width_height("begin ![](/images/headshot.jpg \"Nowucca\" width=200 height=200) end")
    # kramdown_image_width_height("begin ![](/images/headshot.jpg \"Nowucca\") end")
    # print(kramdown_image_width_height("begin ![](/images/headshot.jpg)
    #      ![](/images/headshot.jpg \"Nowucca\" width=200 height=200) end"))
