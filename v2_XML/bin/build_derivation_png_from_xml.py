#!/opt/local/bin/python
# Physics Equation Graph
# Ben Payne <ben.is.located@gmail.com>
# builds the graph of equations as PNG or SVG by reading from databases
# use: python bin/build_connections_graph.py

# files required as input:
#    lib_physics_graph.py
#    connections_database.xml
#    inference_rules_database.xml
#    expressions_database.xml
# output:
#    out_no_labels.png
#    out_with_labels.png

# current bugs:
# if an op is missing, i.e., "lib/images_infrule_png/subXforY.png" then it
# doesn't get built

from xml.dom.minidom import parseString
import lib_physics_graph as physgraf
import yaml  # used to read "config.input"
import os.path
import sys
lib_path = os.path.abspath('../lib')
db_path = os.path.abspath('databases')
output_path = os.path.abspath('output')
sys.path.append(lib_path)  # this has to proceed use of physgraph


# http://stackoverflow.com/questions/6665725/parsing-xml-using-minidom
# import easy to use xml parser called minidom:

# https://yaml-online-parser.appspot.com/
input_stream = file('config.input', 'r')
input_data = yaml.load(input_stream)
extension = input_data["file_extension_string"]
# set to false if you want to make just one graph; then you also need to
# set which graph to make
makeAllGraphs = input_data["makeAllGraphs_boolean"]
if (not makeAllGraphs):
    name_of_set_to_make = input_data["name_of_set_to_make"]
    filename_with_labels = "graph_" + name_of_set_to_make + "_with_labels"
    filename_without_labels = "graph_" + name_of_set_to_make + "_with_labels"
else:  # making all graphs
    filename_with_labels = 'graph_all_with_labels'
    filename_without_labels = 'graph_all_without_labels'

make_graphviz = input_data["make_graphviz_boolean"]
make_graphml = input_data["make_graphml_boolean"]
make_networkx = input_data["make_networkx_boolean"]


eq_pictures = lib_path + '/images_expression_' + extension
op_pictures = lib_path + '/images_infrule_' + extension
feed_pictures = lib_path + '/images_feed_' + extension

connectionsDB = physgraf.parse_XML_file(db_path + '/connections_database.xml')
inference_rulesDB = physgraf.parse_XML_file(
    db_path + '/inference_rules_database.xml')
expressionsDB = physgraf.parse_XML_file(db_path + '/expressions_database.xml')

if (make_graphml):
    graphml_file = open(output_path + '/connections_result.graphml', 'w')
    physgraf.write_header_graphml(graphml_file)

if (make_networkx):
    networkx_file = open(output_path + '/connections_result.py', 'w')
    physgraf.write_header_networkx(networkx_file)

if (make_graphviz):
    graphviz_file = open(output_path + '/connections_result.gv', 'w')
    physgraf.write_header_graphviz(graphviz_file)

input_label_array = []
output_label_array = []

# begin loop through connections
for these_connections in connectionsDB.getElementsByTagName('connection_set'):
    which_connection_set_xml = these_connections.attributes["name"]
    which_connection_set = which_connection_set_xml.value
#   print("which_connection_set="+str(which_connection_set))
#   print("name_of_set_to_make="+str(name_of_set_to_make))
    if ((not makeAllGraphs) and (which_connection_set != name_of_set_to_make)):
        which_connection_set = name_of_set_to_make
        continue  # skip this loop iteration

    for connector in these_connections.getElementsByTagName('connection'):
        infrule_name = physgraf.convert_tag_to_content(
            connector, 'infrule_name', 0)
        inference_rule_label = physgraf.convert_tag_to_content(
            connector, 'infrule_temporary_unique_id', 0)
        if (make_graphviz):
            # http://www.graphviz.org/doc/info/attrs.html#d:image
            #graphviz_file.write(inference_rule_label+" [shape=invtrapezium,color=red,image=\""+op_pictures+"/"+infrule_name+"."+extension+"\",labelloc=b,URL=\"http://google.com\"];\n")
            graphviz_file.write(
                inference_rule_label +
                " [shape=invtrapezium,color=red,image=\"" +
                op_pictures +
                "/" +
                infrule_name +
                "." +
                extension +
                "\"];\n")
        if (make_graphml):
            graphml_file.write(
                '    <node id=\"' +
                inference_rule_label +
                '\"/>\n')
        for input_nodes in connector.getElementsByTagName(
                'input'):  # there may be multiple inputs for a given connection
            #       print('feed:')
            #       print connector.getElementsByTagName('input')[0].toxml()
            for feed_counter in range(
                    len(input_nodes.getElementsByTagName('feed_temporary_unique_id'))):
                feed_temporary_unique_id = physgraf.convert_tag_to_content(
                    input_nodes, 'feed_temporary_unique_id', feed_counter)

                if (make_graphviz):
                    graphviz_file.write(
                        feed_temporary_unique_id +
                        " [shape=ellipse,color=red,image=\"" +
                        feed_pictures +
                        "/" +
                        feed_temporary_unique_id +
                        "." +
                        extension +
                        "\",labelloc=b,URL=\"http://feed.com\"];\n")
                    graphviz_file.write(
                        feed_temporary_unique_id +
                        " -> " +
                        inference_rule_label +
                        "\n")
                if (make_graphml):
                    graphml_file.write(
                        "    <node id=\"" +
                        feed_temporary_unique_id +
                        "\"/>\n")
                    graphml_file.write(
                        "    <edge source=\"" +
                        feed_temporary_unique_id +
                        "\" target=\"" +
                        inference_rule_label +
                        "\"/>\n")
                if (make_networkx):
                    networkx_file.write(
                        'G.add_edge([' + feed_temporary_unique_id + ',' + inference_rule_label + '])\n')
            input_label_array = []
            for expression_counter in range(
                    len(input_nodes.getElementsByTagName('expression_permenant_unique_id'))):
                expression_indx = physgraf.convert_tag_to_content(
                    input_nodes, 'expression_permenant_unique_id', expression_counter)
                input_label_array.append(expression_indx)
                if (make_graphviz):
                    graphviz_file.write(
                        expression_indx +
                        " [shape=ellipse,color=red,image=\"" +
                        eq_pictures +
                        "/" +
                        expression_indx +
                        "." +
                        extension +
                        "\",labelloc=b,URL=\"http://input.com\"];\n")
                    graphviz_file.write(
                        expression_indx + " -> " + inference_rule_label + "\n")
                if (make_graphml):
                    graphml_file.write(
                        "    <node id=\"" + expression_indx + "\"/>\n")
                    graphml_file.write(
                        "    <edge source=\"" +
                        expression_indx +
                        "\" target=\"" +
                        inference_rule_label +
                        "\"/>\n")
                if (make_networkx):
                    networkx_file.write(
                        'G.add_edge([' + expression_indx + ',' + inference_rule_label + '])\n')

        for output_nodes in connector.getElementsByTagName(
                'output'):  # there may be multiple outputs for a given connection
            for expression_counter in range(
                    len(output_nodes.getElementsByTagName('expression_permenant_unique_id'))):
                expression_indx = physgraf.convert_tag_to_content(
                    output_nodes, 'expression_permenant_unique_id', expression_counter)

                # Given a "expression_indx" from connector, get the
                # corresponding latex in statementDB
                expression_latex = physgraf.convert_tpunid_to_latex(
                    expression_indx, expressionsDB, 'expression')

                if (make_graphviz):
                    graphviz_file.write(
                        expression_indx +
                        " [shape=ellipse,color=red,image=\"" +
                        eq_pictures +
                        "/" +
                        expression_indx +
                        "." +
                        extension +
                        "\",labelloc=b,URL=\"http://output.com\"];\n")
                    graphviz_file.write(
                        inference_rule_label + " -> " + expression_indx + "\n")
                if (make_graphml):
                    graphml_file.write(
                        "    <node id=\"" + expression_indx + "\"/>\n")
                    graphml_file.write(
                        "    <edge source=\"" +
                        inference_rule_label +
                        "\" target=\"" +
                        expression_indx +
                        "\"/>\n")
                if (make_networkx):
                    networkx_file.write(
                        'G.add_edge([' + inference_rule_label + ',' + expression_indx + '])\n')
        # reset arrays to be empty for next connection
        feed_array = []
        input_label_array = []
        output_label_array = []

# end loop through connections

if (make_graphml):
    graphml_file.write('  </graph>\n</graphml>\n')
    graphml_file.close()

if (make_networkx):
    networkx_file.write('nx.plot()\n')
    networkx_file.write('plt.show()\n')
    networkx_file.close()

if (make_graphviz):
    physgraf.write_footer_graphviz(graphviz_file)
    graphviz_file.close()
    physgraf.convert_graphviz_to_pictures(
        extension,
        output_path,
        makeAllGraphs,
        which_connection_set,
        filename_with_labels,
        filename_without_labels)

sys.exit("done")
# end of file
