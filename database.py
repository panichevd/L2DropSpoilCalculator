# -*- coding: utf-8 -*-
from __future__ import print_function
import pypyodbc

SELECT_DROP = 1
SELECT_SPOIL = 1

#ITEM_TYPES
SELECT_ACCESORIES = 1
SELECT_ARMORS = 1
SELECT_ARROWS = 1
SELECT_ADENA = 1 #Asset
SELECT_DYES = 1
SELECT_ETC = 1
SELECT_MATERIALS = 1 #Cannot distinguish resources and armor parts
SELECT_POTIONS = 1
SELECT_RECIPES = 1
SELECT_ENCHANTS = 1
SELECT_SPELLBOOKS = 1
SELECT_WEAPONS = 1

#SERVER_RATES
ADENA_RATE = 3
DROP_RATE = 3
SPOIL_RATE = 3

MINIMUM_CHANCE = 0

cursor = 0


class Drop:
    global cursor

    def form_type_selection_expression(self, query_count, type_value):
        expression = ''
        if query_count:
            expression += ' OR '
        else:
            expression += ' AND ('
        return expression + " type LIKE '" + type_value +"'"

    def form_items_query(self):
        query = '''SELECT itemnames.name, type, price FROM items INNER JOIN itemnames '''\
                       + '''ON items.id = itemnames.id WHERE items.id = ''' + str(self.item_id)
        query_count = 0
        if SELECT_ACCESORIES:
            query += self.form_type_selection_expression(query_count, 'Accesories')
            query_count += 1
        if SELECT_ARMORS:
            query += self.form_type_selection_expression(query_count, 'Armors')
            query_count += 1
        if SELECT_ARROWS:
            query += self.form_type_selection_expression(query_count, 'Arrows')
            query_count += 1
        if SELECT_ADENA:
            query += self.form_type_selection_expression(query_count, 'Asset')
            query_count += 1
        if SELECT_DYES:
            query += self.form_type_selection_expression(query_count, 'Dyes')
            query_count += 1
        if SELECT_ETC:
            query += self.form_type_selection_expression(query_count, 'Etc')
            query_count += 1
        if SELECT_ETC:
            query += self.form_type_selection_expression(query_count, 'Materials')
            query_count += 1
        if SELECT_POTIONS:
            query += self.form_type_selection_expression(query_count, 'Potions')
            query_count += 1
        if SELECT_RECIPES:
            query += self.form_type_selection_expression(query_count, 'Recipes')
            query_count += 1
        if SELECT_ENCHANTS:
            query += self.form_type_selection_expression(query_count, 'Scrolls')
            query_count += 1
        if SELECT_SPELLBOOKS:
            query += self.form_type_selection_expression(query_count, 'Spellbooks')
            query_count += 1
        if SELECT_WEAPONS:
            query += self.form_type_selection_expression(query_count, 'Weapons')
            query_count += 1
        if query_count:
            query += ')'
        else:
            return None
        return query + ';'

    def save_item_params(self):
        query = self.form_items_query()
        if query:
            cursor.execute(query)
            if cursor.arraysize == 1:
                result = cursor.fetchone()
                if result:
                    self.name = result[0]
                    self.type = result[1]
                    self.base_price = result[2]
                    return
        self.name = ''
        self.type = ''
        self.base_price = 0

    def adjust_adena_amount(self):
        if self.type == 'Asset':
            self.avg_count *= ADENA_RATE

    def check_mimimal_chance(self):
        if self.chance < MINIMUM_CHANCE:
            self.chance = 0

    def adjust_chance(self, base_chance):
        if self.spoil:
            self.chance = base_chance*SPOIL_RATE
        elif self.type != 'Asset' and self.type != '':
            self.chance = base_chance*DROP_RATE

        if self.chance > 100:
            self.chance = 100

    def get_price(self):
        return self.price

    def __init__(self, query_result):
        self.item_id = query_result[0]
        self.avg_count = (query_result[1] + query_result[2])/2
        self.spoil = query_result[3]
        self.chance = query_result[4]
        self.save_item_params()
        self.adjust_chance(query_result[4])
        self.adjust_adena_amount()
        self.check_mimimal_chance()
        self.price = (self.base_price/2)*(self.chance/100)*self.avg_count
        #will add function allowing customizing prices instead of using base ones


class Mob:
    global cursor

    def __init__(self, query_result):
        self.id = query_result[0]
        self.name = query_result[1]
        self.level = query_result[2]
        self.exp = query_result[3]

    def form_drop_value_query(self):
        query = 'SELECT item_id, min, max, sweep, percentage FROM drops WHERE npc_id = ' + str(self.id)
        additional_condition = ''
        if SELECT_DROP and not SELECT_SPOIL:
            additional_condition = ' AND sweep = 0'
        elif SELECT_SPOIL and not SELECT_DROP:
            additional_condition = ' AND sweep = 1'
        return query + additional_condition + ';'

    def get_drop_value(self):
        if not SELECT_DROP and not SELECT_SPOIL:
            return 0;
        monster_price = 0
        query = self.form_drop_value_query()
        cursor.execute(query)
        for row in cursor.fetchall():
            drop = Drop(row)
            monster_price += drop.get_price()
        return monster_price


def main():
    global cursor
    conn = pypyodbc.win_connect_mdb('l2.mdb')
    cursor = conn.cursor()

    cursor.execute('''SELECT monsters.id, npcnames.name, monsters.level, exp FROM monsters'''\
                   + ''' INNER JOIN npcnames ON monsters.id = npcnames.id'''\
            +''' WHERE monsters.npc = 0 AND monsters.show = True;''')
    for row in cursor.fetchall():
        mob = Mob(row)
        print(mob.name, mob.get_drop_value())
        # Will add saving to list and sorting by lvl here. Also should be able to filter best mobs
        # on level by Adena and Adena Per Exp


    for row in cursor.fetchall():
        for field in row:
            print (field, end=" ")
        print ('')

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()