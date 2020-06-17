import pandas as pd
from utils.Course import Course
import requests
import discord
import xml.etree.ElementTree as ET
from urllib.request import urlopen

classes_offered = pd.read_csv('data/2020-fa.csv')
classes_offered['Class'] = classes_offered['Subject'] + classes_offered['Number'].astype(str)
class_gpa = pd.read_csv('data/uiuc-gpa-dataset.csv')
class_gpa['Class'] = class_gpa['Subject'] + class_gpa['Number'].astype(str)


# Taken from Prof. Wade's reddit-uiuc-bot.
def get_recent_average_gpa(course):
    df = class_gpa[class_gpa["Class"] == course].groupby(
        "Class").agg("sum").reset_index()
    if len(df) == 0:
        return None

    df["Count GPA"] = df["A+"] + df["A"] + df["A-"] + df["B+"] + df["B"] + df["B-"] + \
                      df["C+"] + df["C"] + df["C-"] + df["D+"] + df["D"] + df["D-"] + df["W"]
    df["Sum GPA"] = (4 * (df["A+"] + df["A"])) + (3.67 * df["A-"]) + \
                    (3.33 * df["B+"]) + (3 * df["B"]) + (2.67 * df["B-"]) + \
                    (2.33 * df["C+"]) + (2 * df["C"]) + (1.67 * df["C-"]) + \
                    (1.33 * df["D+"]) + (1 * df["D"]) + (0.67 * df["D-"])

    df["Average GPA"] = df["Sum GPA"] / df["Count GPA"]
    gpa = df["Average GPA"].values[0]

    if gpa is None:
        return 'No data'
    else:
        return str(round(gpa, 2))


async def send_class(channel, course):
    # TODO Add comment about meaning of course
    class_str = course[0].upper() + course[1]
    line = classes_offered.loc[classes_offered['Class'] == class_str]

    if len(line) == 0:
        href_link_to_class = 'https://courses.illinois.edu/cisapp/explorer/catalog/2020/fall/' \
                               + course[0].upper() + '/' + course[1] + '.xml'
        try:
            class_tree = ET.parse(urlopen(href_link_to_class)).getroot()

            class_id = class_tree.attrib['id']  # AAS 100
            # department_code, course_num = course.__get_class(class_id)  # AAS, 100
            label = class_tree.find('label').text  # Intro Asian American Studies
            description = class_tree.find('description').text  # Provided description of the class
            crh = class_tree.find('creditHours').text  # 3 hours.
            deg_attr = ',\n'.join(
                x.text for x in class_tree.iter('genEdAttribute'))  # whatever geneds the class satisfies
            year_term = class_tree.find('termsOffered').find('course').text
            if year_term == 'Fall 2020':
                year_term = 'Offered in Fall 2020.'
            else:
                year_term = 'Most recently offered in ' + year_term

            gpa = get_recent_average_gpa(class_id.upper().replace(' ', ''))
            #  return __get_dict(year_term, class_id, department_code, course_num, label, description, crh, deg_attr)
            message_str = Course(name=class_id, title=label, crh=crh, gpa=gpa, status=year_term,
                                 deg_attr=deg_attr, desc=description)
            await channel.send(embed=message_str.get_embed())

        except:
            await channel.send(class_str + ': Could not find this class.\n')

    else:
        # Get information about a class.
        class_name = line['Name'].iloc[0].replace('&amp;', '&')  # fix issues with the ampersand
        line = line.loc[classes_offered['Class'] == class_str]
        crh = line['Credit Hours'].iloc[0]
        status = line['YearTerm'].iloc[0].strip()
        desc = (line.iloc[0]['Description']).replace(' &amp;', '&')
        deg_attr = line['Degree Attributes'].iloc[0]
        # print(deg_attr)

        if isinstance(deg_attr, str):
            deg_attr = deg_attr.strip()
            deg_attr = deg_attr.replace('and ', '\n').replace('course', '').replace('.', '')
        else:
            deg_attr = ''

        status = 'Offered in Fall 2020.'

        gpa = get_recent_average_gpa(class_str)

        # Make a Class object with all information about the class.
        message_str = Course(class_str, class_name, crh, gpa, status, deg_attr, desc)
        # send embed in channel
        await channel.send(embed=message_str.get_embed())

