import brat_annotations
from brat_annotations import Type
from brat_annotations import Label
from itertools import groupby
import numpy as np
from igraph import *
import codecs
import igraph.remote.gephi as igg

class Stats:
    def __init__(self, annotations=[], is_first_level=False, is_last_level=False, group_characteristic="ALL"):
        self.total = annotations
        self.is_first_level = is_first_level
        self.is_last_level = is_last_level
        self.group_characteristic = group_characteristic
        self.compute_stats()


    def compute_stats(self, with_parts_of_same=True):
        self.total = [self.calculate_span_length(ann) for ann in self.total]
        self.entities = [ann for ann in self.total if ann.type == Type.ENTITY]
        self.relations = [ann for ann in self.total if ann.type == Type.RELATION]
        self.claims = [ann for ann in self.total if ann.label == Label.BACKGROUND_CLAIM or ann.label == Label.OWN_CLAIM]
        self.background_claims = [ann for ann in self.total if ann.label == Label.BACKGROUND_CLAIM]
        self.data = [ann for ann in self.total if ann.label == Label.DATA]
        self.own_claims = [ann for ann in self.total if ann.label == Label.OWN_CLAIM]
        if with_parts_of_same:
            self.parts_of_same = [ann for ann in self.total if ann.label == Label.PARTS_OF_SAME]
        else:
            self.parts_of_same = []
        self.supports =  [ann for ann in self.total if ann.label == Label.SUPPORTS]
        self.contradicts = [ann for ann in self.total if ann.label == Label.CONTRADICTS]
        self.semantically_same = [ann for ann in self.total if ann.label == Label.SEMANTICALLY_SAME]

        if not self.is_last_level:
            self.grouped_by_file = [Stats(annotations=group, group_characteristic=group[0].file, is_last_level=True) for group in self.group_by_file()]
            print("Create Graphs")
            self.create_graphs()


        if self.is_first_level:
            self.grouped_by_domain = [Stats(annotations=group, group_characteristic=group[0].domain) for group in self.group_by_domain()]
            self.grouped_by_publication_type = [Stats(annotations=group, group_characteristic=group[0].publication_type) for group in self.group_by_publication_type()]




    def is_begin_of_part_of(self, component):
        for part_of in self.parts_of_same:
                if component.id == part_of.start.split(":")[1] and component.file == part_of.file:
                    return True
        return False


    #def is_end_of_part_of(self, component):
    #    for part_of in self.parts_of_same:
    #            if component.id == part_of.end.split(":")[1] and component.file == part_of.file:
    #                return True
    #    return False


    def count_is_begin_of_part_of(self, component):
        count = 0
        for part_of in self.parts_of_same:
                if component.id == part_of.start.split(":")[1] and component.file == part_of.file:
                    count = count + 1
        return count


    '''Potential problem only when a single component is referring to two or more other components with parts_of_same but they should actually all belong together;
    but this case is not present (I checked all the three cases in which the count is higher than 1; only luise did this and in all cases its correct)'''
    def remove_part_of_components(self):
        self.total = [component for component in self.total if not self.is_begin_of_part_of(component)]
        self.compute_stats()
        return self.total


    # def retrieve_part_of_target(self, start_component):
    #     for part_of in self.parts_of_same:
    #         if start_component.id == part_of.start.split(":")[1] and start_component.file == part_of.file:
    #             target_id = part_of.end.split(":")[1]
    #             target_file = part_of.file
    #             for candidate in self.entities:
    #                 if candidate.id == target_id and candidate.file == target_file:
    #                     return candidate
    #     return None


    def retrieve_part_of_starts(self, end_component):
        res = []
        for part_of in self.parts_of_same:
            if end_component.id == part_of.end.split(":")[1] and end_component.file == part_of.file:
                start_id = part_of.start.split(":")[1]
                start_file = part_of.file
                for candidate in self.entities:
                    if candidate.id == start_id and candidate.file == start_file:
                        res.append(candidate)
        if len(res) == 0:
            return None
        return res


    def enrich_entities_with_lists(self):
        for entity in self.entities:
            entity.span_list = [{"start": entity.start, "end": entity.end}]
            entity.text_list = [entity.text]
            entity.label_list = [entity.label]
            entity.id_list = [entity.id]


    def retrieve_all_part_of_starts_for_entity(self, entities):
        result = []
        for entity in entities:
            candidates = self.retrieve_part_of_starts(entity)
            if candidates is None:
                result.extend([entity])
            else:
                result.extend([entity] + self.retrieve_all_part_of_starts_for_entity(candidates))
        return result


    def retrieve_all_part_of_starts(self):
        all_starts = []
        for entity in self.entities:
            starts = self.retrieve_all_part_of_starts_for_entity([entity])
            all_starts.append(starts)
        #all_starts_filtered = [starts for starts in all_starts if len(starts) > 1]
        return all_starts


    def find_duplicates(self):
        import collections
        ids = []
        for part in self.resolved_parts:
            for id in part.id_list:
                ids.append((id, part.file))
        ids_2 = []
        for ent in self.total:
            if ent.type == Type.ENTITY:
                ids_2.append((ent.id, ent.file))
        print([(item, count) for item, count in collections.Counter(ids).items() if count > 1])
        print([(item, count) for item, count in collections.Counter(ids_2).items() if count > 1])
        print(str(set(ids).difference(set(ids_2))))
        print(str(set(ids_2).difference(set(ids))))


    def copy_relationships(self, file, old_id, new_id):
        for relationship in self.relations:
            if relationship.start.split(":")[1] == old_id and file==relationship.file:
                relationship.start = relationship.start.split(":")[0] + ":" + new_id
            if relationship.end.split(":")[1] == old_id and file==relationship.file:
                relationship.end = relationship.end.split(":")[0] + ":" + new_id


    def resolve_part_of_relationships(self):
        counts = [(entity, self.count_is_begin_of_part_of(entity)) for entity in self.entities]
        counts_filtered = [(entity,count) for (entity, count) in counts if count > 1 ]
        print(counts_filtered)

        if hasattr(self, 'resolved_parts'):
            self.find_duplicates()
        self.resolved_parts = []

        self.enrich_entities_with_lists()
        total = self.retrieve_all_part_of_starts()
        total = self.group_by_file(total)

        for starts in total:
            parts_grouped = []
            for i,start_a in enumerate(starts):
                found = False
                for j,start_b in enumerate(starts):
                    if all(elem in start_b for elem in start_a) and i != j:
                        found = True
                        break
                if found == False:
                    parts_grouped.append(start_a)
            for part_list in parts_grouped:
                assert(all(elem.file == part_list[0].file for elem in part_list))
                item_to_keep = part_list[0]
                part_list.remove(item_to_keep)
                for elem in part_list:
                    item_to_keep.span_list.append({"start": elem.start, "end": elem.end})
                    item_to_keep.label_list.append(elem.label)
                    item_to_keep.text_list.append(elem.text)
                    item_to_keep.id_list.append(elem.id)
                    self.copy_relationships(file=elem.file, old_id=elem.id, new_id=item_to_keep.id)
                    # todo: search for the relationships and change the identifier
                self.resolved_parts.append(item_to_keep)
        #test_list = []
        #for i, elem in enumerate(resolved_parts):
            #print(str((i, elem.file, elem.text)))
            # TODO: This assertion fails because there is a mistake in the data
            #assert(all(elem.label == label for label in elem.label_list))
            #test_list.extend(elem.text_list)
        #assert(len(test_list) == 13578)
        self.relations = [ann for ann in self.relations if ann.label != Label.PARTS_OF_SAME]
        self.total = self.resolved_parts + self.relations
        self.compute_stats(with_parts_of_same=False)
        return self.resolved_parts

        #for file_stats in self.grouped_by_file:
        #    g = self.create_graph(file_stats.entities, file_stats.parts_of_same)
        #    g.delete_vertices(g.vs.select(_degree_eq=0))
        #    clusters = g.clusters()
        #    print(clusters)


        #starts = self.retrieve_all_part_of_starts()
        #for entity in self.entities:
        #    if self.is_begin_of_part_of(entity):
        #        spans_to_copy = entity.span_list
        #        texts_to_copy = entity.span_list
        #        labels_to_copy = entity.label_list
        #        id_to_copy = entity.id
        #        self.retrieve_part_of_target(entity)
        #    else:
        #        filtered_entities.append()




    def group_to_string(self, f):
        f.write("GROUP: " + self.group_characteristic + "\n")
        f.write("Number of annotations: " + str(len(self.total)) + ", percent: " +str(len(self.total)/len(self.total)) + "\n")
        f.write("\tNumber of entities: " + str(len(self.entities)) + ", percent: " +str(len(self.entities)/len(self.entities)) + "\n")
        f.write("\t\tNumber of claims: " + str(len(self.claims))+ ", percent: " +str(len(self.claims)/len(self.entities)) + "\n")
        f.write("\t\t\tNumber of background_claims: " + str(len(self.background_claims)) + ", percent: " +str(len(self.background_claims)/len(self.entities)) + "\n")
        f.write("\t\t\tNumber of own_claims: " + str(len(self.own_claims)) + ", percent: " +str(len(self.own_claims)/len(self.entities)) + "\n")
        f.write("\t\tNumber of data: " + str(len(self.data))+ ", percent: " +str(len(self.data)/len(self.entities)) + "\n")
        f.write("\tNumber of relations: " + str(len(self.relations)) + ", percent: " +str(len(self.relations)/len(self.relations)) + "\n")
        f.write("\t\tNumber of supports: " + str(len(self.supports)) + ", percent: " +str(len(self.supports)/len(self.relations)) + "\n")
        f.write("\t\tNumber of contradicts: " + str(len(self.contradicts)) + ", percent: " +str(len(self.contradicts)/len(self.relations)) + "\n")
        f.write("\t\tNumber of semantically_same: " + str(len(self.semantically_same)) + ", percent: " +str(len(self.semantically_same)/len(self.relations)) + "\n")
        f.write("\t\tNumber of parts_of_same: " + str(len(self.parts_of_same)) + "\n" + "\n")


        f.write("\tMin, max, avg, median, std span length for entities: " + str(self.calculate_min_max_avg_median_std_span_length(self.entities)) + "\n")
        f.write("\t\tMin, max, avg, median, std span length for claims: " + str(self.calculate_min_max_avg_median_std_span_length(self.claims)) + "\n")
        f.write("\t\t\tMin, max, avg, median, std span length for background_claims: " + str(self.calculate_min_max_avg_median_std_span_length(self.background_claims)) + "\n")
        f.write("\t\t\tMin, max, avg, median, std span length for own_claims: " + str(self.calculate_min_max_avg_median_std_span_length(self.own_claims)) + "\n")
        f.write("\t\tMin, max, avg, median, std span length for data: " + str(self.calculate_min_max_avg_median_std_span_length(self.data)) + "\n\n")

        f.write("Number of files: " + str(len(self.grouped_by_file)) + "\n")
        f.write("\nMin, max, avg, median, std of total per file: " + str(self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "total")) + "\n")
        f.write("\tMin, max, avg, median, std of entities per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "entities")) + "\n")
        f.write("\t\tMin, max, avg, median, std of claims per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "claims")) + "\n")
        f.write("\t\t\tMin, max, avg, median, std of background_claims per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "background_claims")) + "\n")
        f.write("\t\t\tMin, max, avg, median, std of own_claims per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "own_claims")) + "\n")
        f.write("\t\tMin, max, avg, median, std of data per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "data")) + "\n")
        f.write("\tMin, max, avg, median, std of relations per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "relations")) + "\n")
        f.write("\t\tMin, max, avg, median, std of supports relations per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "supports")) + "\n")
        f.write("\t\tMin, max, avg, median, std of contradicts relations per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "contradicts")) + "\n")
        f.write("\t\tMin, max, avg, median, std of semantically_same relations per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "semantically_same")) + "\n")
        f.write("\t\tMin, max, avg, median, std of parts_of_same relations per file: " + str(
            self.get_min_max_avg_median_std_count_for_property(self.grouped_by_file, "parts_of_same")) + "\n" + "\n")


        f.write("For every file: " + "\n")
        for file_graph in self.file_graphs:
            f.write("\tFile: " + str(file_graph["file"]) + "\n")
            f.write("\t\tDiameter of the argumentation graph: " + str(file_graph["diameter"]) + "\n")
            f.write("\t\tUnsupported Claims: " + str(len(file_graph["unsupported_claims"])) + "\n")
            f.write("\t\tStandalone Claims: " + str(len(file_graph["standalone_claims"])) + "\n")
            f.write("\t\tMax in-Degree: " + str(file_graph["max_indegree"]) + "\n")
            f.write("\t\tMax PageRank: " + str(max(file_graph["max_pagerank"])) + "\n")



        # print("\nMin, max, avg, median, std of total per domain: " + str(self.get_min_max_avg_median_for_property(self.grouped_by_domain, "total")))
        # print("\tMin, max, avg, median, std of entities per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "entities")))
        # print("\t\tMin, max, avg, median, std of claims per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "claims")))
        # print("\t\t\tMin, max, avg, median, std of background_claims per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "background_claims")))
        # print("\t\t\tMin, max, avg, median, std of own_claims per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "own_claims")))
        # print("\t\tMin, max, avg, median, std of data per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "data")))
        # print("\tMin, max, avg, median, std of relations per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "relations")))
        # print("\t\tMin, max, avg, median, std of supports relations per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "supports")))
        # print("\t\tMin, max, avg, median, std of contradicts relations per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "contradicts")))
        # print("\t\tMin, max, avg, median, std of semantically_same relations per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "semantically_same")))
        # print("\t\tMin, max, avg, median, std of parts_of_same relations per domain: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_domain, "parts_of_same")))
        #
        #
        # print("\nMin, max, avg, median, std of total per publication_type: " + str(self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "total")))
        # print("\tMin, max, avg, median, std of entities per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "entities")))
        # print("\t\tMin, max, avg, median, std of claims per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "claims")))
        # print("\t\t\tMin, max, avg, median, std of background_claims per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "background_claims")))
        # print("\t\t\tMin, max, avg, median, std of own_claims per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "own_claims")))
        # print("\t\tMin, max, avg, median, std of data per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "data")))
        # print("\tMin, max, avg, median, std of relations per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "relations")))
        # print("\t\tMin, max, avg, median, std of supports relations per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "supports")))
        # print("\t\tMin, max, avg, median, std of contradicts relations per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "contradicts")))
        # print("\t\tMin, max, avg, median, std of semantically_same relations per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "semantically_same")))
        # print("\t\tMin, max, avg, median, std of parts_of_same relations per publication_type: " + str(
        #     self.get_min_max_avg_median_for_property(self.grouped_by_publication_type, "parts_of_same")))

    def calculate_span_length(self, entity):
        if hasattr(entity, "span_list"):
            lengths = [int(span["end"])-int(span["start"]) for span in entity.span_list]
            entity.total_length = sum(lengths)
        else:
            entity.total_length = 0
        return entity
    
    
    def calculate_min_max_avg_median_std_span_length(self, group):
        values = []
        for entity in group:
            values.append(entity.total_length)
        return np.min(values), np.max(values), np.average(values), np.median(values), np.std(values)
        


    def to_string(self):
        ## Eventually also example for semantically same
        with codecs.open("./results/overview.txt", "w", "utf8") as f:
            f.write("GENERAL\n")
            f.write("-------\n")
            self.group_to_string(f)
            f.write("\n\nBY DOMAIN\n")
            f.write("-------\n")
            for group in self.grouped_by_domain:
                group.group_to_string(f)
            f.write("\n\nBY PUBLICATION TYPE\n")
            f.write("-------\n")
            for group in self.grouped_by_publication_type:
                group.group_to_string(f)
            f.close()
        with codecs.open("./results/unsupported_background_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["unsupported_claims"]:
                    if claim["label"] == Label.BACKGROUND_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/unsupported_own_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["unsupported_claims"]:
                    if claim["label"] == Label.OWN_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/standalone_background_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["standalone_claims"]:
                    if claim["label"] == Label.BACKGROUND_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/standalone_own_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["standalone_claims"]:
                    if claim["label"] == Label.OWN_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/max_indegree_background_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["max_indegree_vertices"]:
                    if claim["label"] == Label.BACKGROUND_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/max_indegree_own_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["max_indegree_vertices"]:
                    if claim["label"] == Label.OWN_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/max_pagerank_background_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["max_indegree_vertices"]:
                    if claim["label"] == Label.BACKGROUND_CLAIM:
                        self.output_component(f, claim)
            f.close()
        with codecs.open("./results/max_pagerank_own_claims.txt", "w", "utf8") as f:
            for file_graph in self.file_graphs:
                for claim in file_graph["max_pagerank_vertices"]:
                    if claim["label"] == Label.OWN_CLAIM:
                        self.output_component(f, claim)
            f.close()



    ''' Groups a given list by computer graphics domain'''
    def group_by_domain(self):
        for ann in self.total:
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
        self.total.sort(key=keyfunc)
        for k, g in groupby(self.total, keyfunc):
            argument_groups.append(list(g))
        return argument_groups


    ''' Groups a given list by file name'''
    def group_by_file(self, lst=None):
        def keyfunc(val):
            if type(val) == list:
                return val[0].file
            else:
                return val.file

        argument_groups = []
        #
        if lst is None:
            lst = self.total
        lst.sort(key=keyfunc)
        for k, g in groupby(lst, keyfunc):
            argument_groups.append(list(g))
        return argument_groups


    '''
    This assignment to publication types was made by us based on the bibliographic information that could be found
    '''
    def group_by_publication_type(self):
        for ann in self.total:
            if ann.file in ["A03.ann", "A04.ann", "A05.ann", "A07.ann", "A10.ann", "A12.ann", "A13.ann",
                            "A15.ann", "A16.ann", "A17.ann", "A19.ann", "A20.ann", "A21.ann", "A22.ann",
                            "A25.ann", "A26.ann", "A27.ann", "A28.ann", "A29.ann", "A30.ann", "A31.ann",
                            "A33.ann", "A36.ann", "A37.ann", "A40.ann"]:
                ann.publication_type = "JOURNAL_ARTICLE"
            elif ann.file in ["A01.ann","A02.ann", "A06.ann", "A08.ann", "A09.ann", "A11.ann", "A14.ann", "A18.ann",
                              "A23.ann", "A32.ann", "A34.ann", "A35.ann", "A38.ann", "A39.ann"]:
                ann.publication_type = "CONFERENCE_PAPER"
            elif ann.file in ["A24.ann"]:
                ann.publication_type = "TECHNICAL_REPORT"

        def keyfunc(val):
            return val.publication_type

        argument_groups = []
        self.total.sort(key=keyfunc)
        for k, g in groupby(self.total, keyfunc):
            argument_groups.append(list(g))
        return argument_groups


    '''
    Computes Min, max, avg, median, std for a group of stats given a certain component type
    '''
    def get_min_max_avg_median_std_count_for_property(self, grouped_stats, prop):
        values = []
        for stats in grouped_stats:
            values.append(len(getattr(stats,prop)))
        return np.min(values), np.max(values), np.average(values), np.median(values), np.std(values)


    '''
    Creates a file graph
    '''
    def create_graphs(self, grouped_by_file=[]):
        self.file_graphs = []
        if len(grouped_by_file) == 0:
            grouped_by_file = self.grouped_by_file
        for file_stats in grouped_by_file:
            try:
                g = self.create_graph(file_stats.entities, file_stats.relations)

                #self.file_graphs.append(
                #    {"file": file_stats.entities[0].file, "graph": g, "unsupported_claims": isolated_vertices})
                graph_stats = self.compute_graph_stats(g)
                graph_stats["file"] = file_stats.entities[0].file
                self.file_graphs.append(graph_stats)
            except Exception as e:
                print(e)


    def compute_graph_stats(self, g):
        unsupported_claims_indices = g.vs.select(_indegree_eq=0, label_in=[Label.BACKGROUND_CLAIM, Label.OWN_CLAIM]).indices
        unsupported_claims = self.vertex_index_to_vertex(g, unsupported_claims_indices)
        standalone_claims_indices = g.vs.select(_degree_eq=0, label_in=[Label.BACKGROUND_CLAIM, Label.OWN_CLAIM]).indices
        standalone_claims = self.vertex_index_to_vertex(g, standalone_claims_indices)
        diameter = g.diameter(directed=True, unconn=True)
        max_indegree = np.max(g.indegree())
        max_indegree_indices = g.vs.select(_indegree = max_indegree).indices
        max_indegree_vertices = self.vertex_index_to_vertex(g, max_indegree_indices)
        max_pagerank = g.pagerank(directed=True)
        max_pagerank_indices = np.argmax(g.pagerank(directed=True))
        max_pagerank_vertices = self.vertex_index_to_vertex(g, max_pagerank_indices)
        return {"graph": g, "unsupported_claims": unsupported_claims, "standalone_claims": standalone_claims,"diameter": diameter, "max_indegree": max_indegree,
                "max_indegree_vertices":max_indegree_vertices, "max_pagerank": max_pagerank, "max_pagerank_vertices": max_pagerank_vertices}



    def vertex_id_to_index(self, vertices, id):
        for i, vertex in enumerate(vertices):
            if vertex.id == id:
                return i


    def vertex_index_to_vertex(self, g, indices):
        vertices = []
        if not isinstance(indices, list):
            indices = [indices]
        for i in indices:
            vertices.append(g.vs[i])
        return vertices


    def output_component(self, f, component):
        f.write("File: " + str(component["file"]) + "\t")
        f.write("Ids: " + str(component["id_list"]) + "\t")
        f.write("Spans: " + str(component["span_list"]) + "\t")
        f.write("Texts: " + str(component["text_list"]) + "\n")


    def create_graph(self, entities, relations):
        g = Graph(directed=True)
        vertices = entities

        ### We exclude the semantically_same relationships here because for the graph stats they are not relevant
        ## TODO: Verify this
        relations = [relation for relation in relations if relation.label != Label.SEMANTICALLY_SAME]

        g.add_vertices(len(vertices))
        g.vs['id'] = [entity.id for entity in vertices]
        g.vs['label'] = [entity.label for entity in vertices]
        g.vs['text'] = [entity.text for entity in vertices]
        g.vs['file'] = [entity.file for entity in vertices]
        g.vs['start'] = [entity.start for entity in vertices]
        g.vs['end'] = [entity.end for entity in vertices]
        g.vs['type'] = [entity.type for entity in vertices]
        g.vs['span_list'] = [entity.span_list if hasattr(entity, 'span_list') else [] for entity in vertices]
        g.vs['label_list'] = [entity.label_list if hasattr(entity, 'label_list') else [] for entity in vertices]
        g.vs['text_list'] = [entity.text_list if hasattr(entity, 'text_list') else [] for entity in vertices]
        g.vs['id_list'] = [entity.id_list if hasattr(entity, 'id_list') else [] for entity in vertices]


        edges = []
        edge_labels = []
        edge_types = []
        for edge in relations:
            begin_vertex = self.vertex_id_to_index(vertices, edge.start.split("Arg1:")[1])
            end_vertex = self.vertex_id_to_index(vertices, edge.end.split("Arg2:")[1])
            if begin_vertex is not None and end_vertex is not None:
                edges.append((begin_vertex, end_vertex))
                edge_labels.append(edge.label)
                edge_types.append(edge.type)
            #else:
            #    print("Vertex is None")
        #print(edges)
        #if len(edges) == 0:
        #    print("No edges")
        g.add_edges(edges)
        g.es['label'] = edge_labels
        g.es['type'] = edge_types
        # important functions: g.degree(), g.pagerank(), g.vs(label_eq=Label.BACKGROUND_CLAIM)
        # layout = g.layout_lgl()
        # plot(g, target="./plots/" + file_stats.entities[0].file + "2.pdf", layout=layout)
        # Send to Gephi
        # gephi = igg.GephiConnection()
        # streamer = igg.GephiGraphStreamer()
        # streamer.post(g, gephi)
        return g

#def print_general_stats(annotations):
#    stats = Stats(annotations=annotations, is_first_level=True)
#    stats.to_string()


def print_parts_of_same_resolved_stats(annotations):
    stats = Stats(annotations=annotations, is_first_level=True)
    stats.resolve_part_of_relationships()
    #stats.remove_part_of_components()
    stats.to_string()



def main():
    annotations = brat_annotations.parse_annotations("./compiled_corpus")
    print_parts_of_same_resolved_stats(annotations=annotations)
    #annotations = group_by_file(annotations)
    #for group in annotations:
    #    print(group[0].file)
    #    analyze_annotations(annotations=group)
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