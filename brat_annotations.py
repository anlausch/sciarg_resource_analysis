import os
import codecs
from enum import Enum

class Type(Enum):
    ENTITY = 1
    RELATION = 2

class Label(Enum):
    BACKGROUND_CLAIM = 1
    OWN_CLAIM = 2
    DATA = 3
    SUPPORTS = 4
    CONTRADICTS = 5
    PARTS_OF_SAME = 6
    SEMANTICALLY_SAME = 7



class Annotation:
    def __init__(self, id, label, start, end, file, text=""):
        # assign id
        self.id = id

        # assign type
        if id[0] == 'T':
            self.type = Type.ENTITY
        elif id[0] == 'R':
            self.type = Type.RELATION

        # assign label
        if label == "background_claim":
            self.label = Label.BACKGROUND_CLAIM
        elif label == "own_claim":
            self.label = Label.OWN_CLAIM
        elif label == "data":
            self.label = Label.DATA
        elif label == "supports":
            self.label = Label.SUPPORTS
        elif label == "contradicts":
            self.label = Label.CONTRADICTS
        elif label == "parts_of_same":
            self.label = Label.PARTS_OF_SAME
        elif label == "semantically_same":
            self.label = Label.SEMANTICALLY_SAME

        # assign the rest
        if self.type == Type.ENTITY:
            self.start = int(start)
            self.end = int(end)
        else:
            self.start = start
            self.end = end
        self.text = text
        self.file = file

        self.matched = False


    def to_string(self):
        if self.type == Type.ENTITY:
            type = "Argumentative component annotated: " + str(self.label) + "\n"
            id = "\tId is: " + str(self.id) + "\n"
            range_s = "\tSpan starts on character position: " + str(self.start) + "\n"
            range_e = "\tSpan ends on character position: " + str(self.end) + "\n"
            text = "\tTextual content is: " + str(self.text) + "\n"
            file = "\tIn file: " + str(self.file) + "\n"

            final = type + id + range_s + range_e + text + file + "\n"
        elif self.type == Type.RELATION:
            type = "Argumentative relation annotated: " + str(self.label) + "\n\n"
            range_s = "\tStarting from component: " + str(self.start) + "\n"
            range_e = "\tEnding at component: " + str(self.end) + "\n"
            file = "\tIn file: " + str(self.file) + "\n"

            final = type + range_s + range_e + file + "\n"

        return final



def parse_annotations(path):
    annotations = []
    for subdir, dirs, files in os.walk(path):
        for file in files:
            if '.ann' in file:
                with codecs.open(os.path.join(subdir, file), mode="r", encoding="utf8") as ann_file:
                    for line in ann_file:
                        try:
                            # TODO: This is an extension to our other paper
                            id, info, text = line.split("\t")

                            label, start, end = info.split(" ")
                            file = file
                            annotations.append(Annotation(id=id, label=label, start=start, end=end, file=file, text=text))
                            #

                        except Exception as e:
                            # we ignore errors here because brat also shows these as errors and we adviced our annotators to resolve these with parts_of_same
                            #label, start, middle, end = info.split(" ")
                            #middle_start, middle_end = middle.split(";")
                            #if(int(middle_end)-int(middle_start) != 1):
                            #    print("Problem")
                            #file = file
                            #annotations.append(
                            #    Annotation(id=id, label=label, start=start, end=end, file=file, text=text))
                            continue
                            #print("\n")
                            #print(e)
                            #print(file)
                            #print(line)
                            #print("\n")

    return annotations