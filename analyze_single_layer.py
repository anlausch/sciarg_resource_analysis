import brat_annotations
from brat_annotations import Type
from brat_annotations import Label
from itertools import groupby

def is_begin_of_part_of(entity, relations_parts_of):
    for part_of in relations_parts_of:
            if entity.id == part_of.start.split(":")[1] and entity.file == part_of.file:
                return True
    return False

def count_is_begin_of_part_of(entity, relations_parts_of):
    count = 0
    for part_of in relations_parts_of:
            if entity.id == part_of.start.split(":")[1] and entity.file == part_of.file:
                count = count + 1
    return count

'''Potential problem only when a single component is referring to two or more other components with parts_of_same but they should actually all belong together;
but this case is not present (I checked all the three cases in which the count is higher than 1; only luise did this and in all cases its correct)'''
def remove_part_of_components(argument_annotations):
    entities = [arg for arg in argument_annotations if arg.type == Type.ENTITY]
    relations_parts_of = [arg for arg in argument_annotations if arg.type == Type.RELATION and arg.label == Label.PARTS_OF_SAME]
    filtered_entities = [entity for entity in entities if not is_begin_of_part_of(entity, relations_parts_of)]
    return filtered_entities


def analyze_annotations(annotations):
    print("Number of annotations: " + str(len(annotations)))
    entities = [ann for ann in annotations if ann.type == Type.ENTITY]
    print("\tNumber of entities: " + str(len(entities)))
    claims = [ann for ann in annotations if ann.label == Label.BACKGROUND_CLAIM or ann.label == Label.OWN_CLAIM]
    print("\t\tNumber of claims: " + str(len(claims)))
    background_claims = [ann for ann in annotations if ann.label == Label.BACKGROUND_CLAIM]
    print("\t\t\tNumber of background_claims: " + str(len(background_claims)))
    own_claims = [ann for ann in annotations if ann.label == Label.OWN_CLAIM]
    print("\t\t\tNumber of own_claims: " + str(len(own_claims)))
    data = [ann for ann in annotations if ann.label == Label.DATA]
    print("\t\tNumber of data: " + str(len(data)))
    relations = [ann for ann in annotations if ann.type == Type.RELATION]
    print("\tNumber of relations: " + str(len(relations)))
    supports = [ann for ann in annotations if ann.label == Label.SUPPORTS]
    print("\t\tNumber of supports: " + str(len(supports)))
    contradicts = [ann for ann in annotations if ann.label == Label.CONTRADICTS]
    print("\t\tNumber of contradicts: " + str(len(contradicts)))
    parts_of_same = [ann for ann in annotations if ann.label == Label.PARTS_OF_SAME]
    print("\t\tNumber of parts_of_same: " + str(len(parts_of_same)))
    semantically_same = [ann for ann in annotations if ann.label == Label.SEMANTICALLY_SAME]
    print("\t\tNumber of semantically_same: " + str(len(semantically_same)))


def group_by_domain(annotations):
    for ann in annotations:
        if ann.file in ["A01.ann", "A02.ann", "A03.ann", "A04.ann", "A05.ann", "A06.ann", "A07.ann", "A08.ann",
                        "A09.ann", "A10.ann"]:
            ann.domain= "SKINNING"
        elif ann.file in ["A11.ann", "A12.ann", "A13.ann", "A14.ann", "A15.ann", "A16.ann", "A17.ann", "A18.ann",
                        "A19.ann", "A20.ann"]:
            ann.domain = "MOTION"
        elif ann.file in ["A21.ann", "A22.ann", "A23.ann", "A24.ann", "A25.ann", "A26.ann", "A27.ann", "A28.ann",
                        "A29.ann", "A30.ann"]:
            ann.domain = "FLUID_SIMULATION"
        elif ann.file in ["A31.ann", "A32.ann", "A33.ann", "A34.ann", "A35.ann", "A36.ann", "A37.ann", "A38.ann",
                        "A39.ann", "A40.ann"]:
            ann.domain = "CLOTH_SIMULATION"

    def keyfunc(val):
        return val.domain

    argument_groups = []
    #
    for k, g in groupby(annotations, keyfunc):
        argument_groups.append(list(g))
    return argument_groups



def group_by_file(annotations):
    def keyfunc(val):
        return val.file

    argument_groups = []
    #
    for k, g in groupby(annotations, keyfunc):
        argument_groups.append(list(g))
    return argument_groups



def main():
    annotations = brat_annotations.parse_annotations("./compiled_corpus")
    annotations = group_by_domain(annotations)
    for group in annotations:
        print(group[0].domain)
        analyze_annotations(annotations=group)
    #filtered_entities = remove_part_of_components(annotations)
    #analyze_annotations(filtered_entities)
    #entities = [arg for arg in annotations if arg.type == Type.ENTITY]
    #relations_parts_of = [arg for arg in annotations if arg.type == Type.RELATION and arg.label == Label.PARTS_OF_SAME]
    #counts = [(entity, count_is_begin_of_part_of(entity, relations_parts_of)) for entity in entities]
    #counts_filtered = [(entity,count) for (entity, count) in counts if count > 1 ]
    #print(len(counts_filtered))
    #print([(entity.to_string(),count) for (entity, count) in counts_filtered])

if __name__=="__main__":
    main()