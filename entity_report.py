import json  # Import the json module for working with JSON files
from datetime import datetime  # Import the datetime module for working with dates and times
class Entity:
    def __init__(self, dbConfig, config_file, cur, principalfk, allMap, principalMap=None):
        self.dbConfig = dbConfig
        self.config_file = config_file
        self.cur = cur
        with open(config_file, 'r', encoding='utf-8') as file:
            configs_data = json.load(file)
        self.fields = configs_data["gh_fields"]
        self.mapfields = configs_data["gh_mapfields"]
        self.id_fields = configs_data["id_fields"]
        self.audit_fields = configs_data["audit_fields"]
        mainfields = ["b_classname", "b_frombatchid", "b_tobatchid", "audit_finalization_date", "b_creator", "b_credate", "b_updator", "b_upddate"]
        self.main_fields = self.id_fields + mainfields + self.audit_fields
        self.order_fields = configs_data["order_fields"]
        self.tableName = configs_data["table_name"]
        self.nFields = len(self.fields)
        self.nMain_Fields = len(self.main_fields)
        self.EntityLines = []
        principal = configs_data["principal"]
        self.principalFK = principalfk
        self.allMap = allMap
        if principal:
            self.map_principal = None
        else:
            self.map_principal = principalMap
    def getEntityLines(self):
        all_fields = self.main_fields + self.fields
        all_fields_str = ', '.join(all_fields)
        order_fields_str = ', '.join(self.order_fields)
        query = f"SELECT {all_fields_str} FROM {self.tableName} ORDER BY {order_fields_str} ASC"
        self.cur.execute(query)
        results = self.cur.fetchall()
        map = self.generate_map(results)
        for changes in map.values():
            self.get_differences(changes)
        return self.EntityLines
    def generate_map(self, data):
        entity_cod_map = {}
        for line in data:
            entity_cod = line[0]
            if entity_cod in entity_cod_map:
                entity_cod_map[entity_cod].append(line)
            else:
                entity_cod_map[entity_cod] = [line]
        return entity_cod_map
    def get_differences(self, changes):
        all_changes = []
        all_changes.append(self.get_creation_records(changes[0]))
        for i in range(1, len(changes)):
            all_changes.append(self.get_differences_two_lines(changes[i], changes[i - 1]))
            i = i + 1
    def get_creation_records(self, record):
        clinom = self.get_princiaplValue ( record)
        updator = record[self.f_index(self.audit_fields[2])] or record[self.f_index(self.audit_fields[0])] or record[ self.f_index("b_updator")] or record[self.f_index("b_creator")]
        updator_date = record[self.f_index(self.audit_fields[3])] or record[ self.f_index(self.audit_fields[1])] or record[self.f_index("b_upddate")] or record[ self.f_index("b_credate")]
        updator_date_str = updator_date.strftime("%Y-%m-%d %H:%M:%S")
        final = (record[self.f_index("audit_finalization_date")] or datetime(updator_date.year, updator_date.month, updator_date.day, 23, 59, 59, 0)).strftime( "%Y-%m-%d %H:%M:%S")
        for index in range(self.nMain_Fields, self.nMain_Fields + self.nFields):
            if record[index] is not None:
                db_fieldname = self.fields[index - self.nMain_Fields]
                fieldname = self.mapfields[index - self.nMain_Fields]
                entity = record[ self.f_index ( "b_classname") ]
                self.EntityLines.append( [entity, clinom, "Creation", fieldname, None, self.get_fieldValue( db_fieldname, record[index]), updator, updator_date_str, final])
    def get_differences_two_lines(self, current, previous):
        clinom = self.get_princiaplValue ( current)
        updator = current[self.f_index(self.audit_fields[2])] or current[self.f_index(self.audit_fields[0])] or current[self.f_index("b_updator")] or current[self.f_index("b_creator")]
        updator_date = current[self.f_index(self.audit_fields[3])] or current[self.f_index(self.audit_fields[1])] or current[self.f_index("b_upddate")] or current[self.f_index("b_credate")]
        updator_date_str = updator_date.strftime("%Y-%m-%d %H:%M:%S")
        final = (current[self.f_index("audit_finalization_date")] or datetime(updator_date.year, updator_date.month, updator_date.day, 23, 59, 59, 0)).strftime( "%Y-%m-%d %H:%M:%S")
        for index in range(self.nMain_Fields, self.nMain_Fields + self.nFields - 1):
            if current[index] != previous[index]:
                db_fieldname = self.fields[index - self.nMain_Fields]
                fieldname = self.mapfields[index - self.nMain_Fields]
                entity = current[ self.f_index ( "b_classname") ]
                self.EntityLines.append( [entity, clinom, "Update", fieldname, self.get_fieldValue( db_fieldname, previous[index]), self.get_fieldValue( db_fieldname, current[index]), updator, updator_date_str, final])
    def f_index(self, field_name):
        return self.main_fields.index(field_name)
    def get_princiaplValue ( self, record):
        princiaplValue = ""
        if self.map_principal is None:
            princiaplValue = record[self.nMain_Fields]
        else:
            try:
                foreignKey = self.id_fields[1]
                valueForeignKey = record[self.f_index ( foreignKey)]
                if foreignKey == self.principalFK:
                    princiaplValue = self.map_principal[valueForeignKey]
                else:
                    princiaplValue = self.map_principal[self.get_fieldValue ( foreignKey, valueForeignKey)]
            except Exception as e:
                princiaplValue = "NOT FOUND"
        return princiaplValue
    def get_fieldValue ( self, field_name, currentValue):
        map = {}
        if field_name in self.allMap:
            map = self.allMap[field_name]
            if currentValue in map:
                return map[currentValue]
        return currentValue