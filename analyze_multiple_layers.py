import load_conll
import numpy as np
from sklearn.cross_decomposition import CCA
import codecs
import pandas as pd
from sklearn.metrics import mutual_info_score
import matplotlib.pyplot as plt


class CorrelationMatrix(object):
    """
    Correlation matrix.
    """

    def __init__(self, labels_a=None, labels_b=None, occurences_a=None, occurences_b=None):
        # rows are true labels, columns predictions
        self.matrix = np.zeros(shape=(len(labels_a), len(labels_b)))
        self.labels_a = labels_a
        self.labels_b = labels_b

        if len(occurences_a) != len(occurences_b):
            raise ValueError("Predictions and gold labels do not have the same count.")
        else:
            for i in range(len(occurences_a)):
                indices_occurence_a = [labels_a.index(label) for label in occurences_a[i]]
                indices_occurence_b = [labels_b.index(label) for label in occurences_b[i]]

                for index_a in indices_occurence_a:
                    for index_b in indices_occurence_b:
                        self.matrix[index_a][index_b] += 1


    def to_string(self, name):
        with codecs.open("results/correlation_matrix_" + name + ".txt", "w", "utf8") as f:
            f.write("\t")
            for label in self.labels_b:
                label = label.strip()
                f.write(label + "\t")
            f.write("\n")
            for row_label, row in zip(self.labels_a, self.matrix):
                f.write('%s\t[%s]' % (row_label, '\t'.join('%03s' % i for i in row)))
                f.write("\n")



def port_annotations_to_sentence_level(annotations):
    sentence_annotations = []
    for sentence in annotations:
        sentence_annotations.append(list(set(sentence)))
    return sentence_annotations


def canonical_correlation_analysis(occurences_a, occurences_b):
    occurences_a = pd.Series(occurences_a, dtype="category")
    occurences_a = pd.get_dummies(occurences_a)
    occurences_b = pd.DataFrame.from_items(occurences_b)
    occurences_b = pd.get_dummies(occurences_b)
    cca = CCA(n_components=1)
    cca.fit(occurences_a, occurences_b)
    return cca.score(occurences_a, occurences_b)


def mutual_information(occurences_a, occurences_b):
    score = mutual_info_score(occurences_a, occurences_b)
    return score

def information_theoretic_measures(y_arg, y_rhet,y_citation, y_aspect, y_summary):
    y_arg = port_annotations_to_sentence_level(y_arg)
    y_rhet = port_annotations_to_sentence_level(y_rhet)
    y_aspect = port_annotations_to_sentence_level(y_aspect)
    y_summary = port_annotations_to_sentence_level(y_summary)
    y_citation = port_annotations_to_sentence_level(y_citation)

    with codecs.open("results/mutual_information.txt", "w", "utf8") as f:
        f.write("Argumentation & Discourse: ")
        f.write(str(mutual_info_score(y_arg, y_rhet)) + "\n")
        f.write("Argumentation & Aspect: ")
        f.write(str(mutual_info_score(y_arg, y_aspect)) + "\n")
        f.write("Argumentation & Summary: ")
        f.write(str(mutual_info_score(y_arg, y_summary)) + "\n")
        f.write("Argumentation & Citation Context: ")
        f.write(str(mutual_info_score(y_arg, y_citation)) + "\n")

        f.write("Discourse & Aspect: ")
        f.write(str(mutual_info_score(y_rhet, y_aspect)) + "\n")
        f.write("Discourse & Summary: ")
        f.write(str(mutual_info_score(y_rhet, y_summary)) + "\n")
        f.write("Discourse & Citation Context: ")
        f.write(str(mutual_info_score(y_rhet, y_citation)) + "\n")


        f.write("Aspect & Summary: ")
        f.write(str(mutual_info_score(y_aspect, y_summary)) + "\n")
        f.write("Aspect & Citation Context: ")
        f.write(str(mutual_info_score(y_aspect, y_citation)) + "\n")

        f.write("Summary & Citation Context: ")
        f.write(str(mutual_info_score(y_summary, y_citation)) + "\n")
        f.write("Discourse & Argumentation (sanity check): ")
        f.write(str(mutual_info_score(y_rhet, y_arg)) + "\n")




def compute_correlation_matrices(y_arg, y_rhet,y_citation, y_aspect, y_summary):

    y_arg = port_annotations_to_sentence_level(y_arg)
    y_rhet = port_annotations_to_sentence_level(y_rhet)
    y_aspect = port_annotations_to_sentence_level(y_aspect)
    y_summary = port_annotations_to_sentence_level(y_summary)
    y_citation = port_annotations_to_sentence_level(y_citation)


    cm_arg_rhet = CorrelationMatrix(labels_a=list(set([item for sublist in y_arg for item in sublist])),
                                    labels_b=list(set([item for sublist in y_rhet for item in sublist])),
                                    occurences_a=y_arg, occurences_b=y_rhet)
    cm_arg_rhet.to_string("arg_rhet")

    cm_arg_cit = CorrelationMatrix(labels_a=list(set([item for sublist in y_arg for item in sublist])),
                                    labels_b=list(set([item for sublist in y_citation for item in sublist])),
                                    occurences_a=y_arg, occurences_b=y_citation)
    cm_arg_cit.to_string("arg_cit")

    cm_arg_summary = CorrelationMatrix(labels_a=list(set([item for sublist in y_arg for item in sublist])),
                                    labels_b=list(set([item for sublist in y_summary for item in sublist])),
                                    occurences_a=y_arg, occurences_b=y_summary)
    cm_arg_summary.to_string("arg_summary")

    cm_arg_aspect = CorrelationMatrix(labels_a=list(set([item for sublist in y_arg for item in sublist])),
                                    labels_b=list(set([item for sublist in y_aspect for item in sublist])),
                                    occurences_a=y_arg, occurences_b=y_aspect)
    cm_arg_aspect.to_string("arg_aspect")

    print("Process finished")


def plot_sentence_lengths(x):
    lengths = [len(sentence) for sentence in x]
    plot = plt.hist(lengths)
    plt.show()

def main():
    x, y_arg, y_rhet, y_aspect, y_summary, y_citation = load_conll.load_data_multiple("./annotations_conll_final")
    # plot_sentence_lengths(x)
    #print("Number of sentences with more than 200 tokens: " + str(len([len(sentence) for sentence in x if len(sentence) > 200])))
    #print(str(len([len(sentence) for sentence in x if len(sentence) > 200])/len(x)))
    compute_correlation_matrices(y_arg=y_arg, y_rhet=y_rhet, y_citation=y_citation, y_aspect=y_aspect, y_summary=y_summary)
    #print(canonical_correlation_analysis(y_arg, y_rhet))
    information_theoretic_measures(y_arg=y_arg, y_rhet=y_rhet, y_citation=y_citation, y_aspect=y_aspect, y_summary=y_summary)

if __name__=="__main__":
    main()