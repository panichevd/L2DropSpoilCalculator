# -*- coding: utf-8 -*-
from __future__ import print_function
import pypyodbc

SELECT_DROP = 1
SELECT_SPOIL = 1

SELECT_MIN_LEVEL = 40
SELECT_MAX_LEVEL = 50

#ITEM_TYPES
SELECT_ACCESORIES = 0
SELECT_ARMORS = 0
SELECT_ARROWS = 0
SELECT_ADENA = 1 #Asset
SELECT_DYES = 1
SELECT_ETC = 1
SELECT_MATERIALS = 1 #Cannot distinguish resources and armor parts
SELECT_POTIONS = 1
SELECT_RECIPES = 1
SELECT_ENCHANTS = 1
SELECT_SPELLBOOKS = 1
SELECT_WEAPONS = 0

#SERVER_RATES
ADENA_RATE = 3
DROP_RATE = 3
SPOIL_RATE = 3

#MINIMUM VALUES
MINIMUM_CHANCE = 0
MINIMUM_DROP_VALUE = 20000
MAXIMUM_DROP_VALUE = 300000 #Temprorary to get raid bosses out of results

#CUSTOMIZED PRICES
customized_prices = [
    ('Adamantine Nugget', 50000),
    ('Animal Bone', 5000),
    ('Animal Skin', 1350),
    ('Charcoal', 2000),
    ('Coal', 5000),
    ('Cokes', 30000),
    ('Cord', 5000),
    ('Coarse Bone Powder', 50000),
    ('Crafted Leather', 75000),
    ('Durable Metal Plate', 400000),
    ('Enria', 270000),
    ('Iron Ore', 6000),
    ('Leather', 8000),
    ('Metallic Fiber', 5000),
    ('Metallic Thread', 40000),
    ('Mithril Ore', 65000),
    ('Oriharukon Ore', 100000),
    ('Steel', 55000),
    ('Stone of Purity', 105000),
    ('Varnish', 8000),
    ('Asofe', 70000), #?
    ('Thons', 70000), #?
    ('Mold Hardener', 400000),
    ('Mold Glue', 70000), #?

    ('Blue Seal Stone', 12),
    ('Green Seal Stone', 20),
    ('Red Seal Stone', 40),

    ('Scroll: Enchant Armor (Grade D)', 25000),
    ('Scroll: Enchant Armor (Grade C)', 35000),
    ('Scroll: Enchant Armor (Grade B)', 50000),

    ('Scroll: Enchant Weapon (Grade D)', 800000),
    ('Scroll: Enchant Weapon (Grade C)', 3500000),
    ('Scroll: Enchant Weapon (Grade B)', 2000000)
]

#Sort by
SORT_BY_LEVEL = 1
SORT_BY_DROP = 2
SORT_TYPE = SORT_BY_DROP

cursor = 0


class Drop:
    global cursor

    def form_type_selection_expression(self, query_count, type_value):
        expression = ''
        if query_count:
            expression += ' OR '
        else:
            expression += ' AND ('
        return expression + " type LIKE '" + type_value + "'"

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

    def check_mimimum_chance(self):
        if self.chance < MINIMUM_CHANCE:
            self.chance = 0

    def count_price(self):
        for custom_price in customized_prices:
            if self.name == custom_price[0]:
                self.price = custom_price[1]
                return
        self.price = self.base_price/2

    def adjust_chance(self, base_chance):
        if self.spoil:
            self.chance = base_chance*SPOIL_RATE
        elif self.type != 'Asset' and self.type != '':
            self.chance = base_chance*DROP_RATE
        else:
            self.chance = base_chance

        if self.chance > 100:
            self.chance = 100

    def get_value(self):
        return self.value

    def __init__(self, query_result):
        self.item_id = query_result[0]
        self.avg_count = (query_result[1] + query_result[2])/2
        self.spoil = query_result[3]
        self.chance = query_result[4]
        self.save_item_params()
        self.adjust_chance(query_result[4])
        self.adjust_adena_amount()
        self.check_mimimum_chance()
        self.count_price()
        self.value = self.price*(self.chance/100)*self.avg_count


class Mob:
    global cursor

    def __init__(self, query_result):
        self.id = query_result[0]
        self.name = query_result[1]
        self.level = query_result[2]
        self.exp = query_result[3]
        self.save_drop_value()

    def __getitem__(self, item):
        return self[item]

    def form_drop_value_query(self):
        query = 'SELECT item_id, min, max, sweep, percentage FROM drops WHERE npc_id = ' + str(self.id)
        additional_condition = ''
        if SELECT_DROP and not SELECT_SPOIL:
            additional_condition = ' AND sweep = 0'
        elif SELECT_SPOIL and not SELECT_DROP:
            additional_condition = ' AND sweep = 1'
        return query + additional_condition + ';'

    def save_drop_value(self):
        if not SELECT_DROP and not SELECT_SPOIL:
            return 0;
        self.monster_price = 0
        query = self.form_drop_value_query()
        cursor.execute(query)
        for row in cursor.fetchall():
            drop = Drop(row)
            self.monster_price += drop.get_value()

    def get_drop_value(self):
        return self.monster_price


def compare_by_drop(item1, item2):
    if item1.get_drop_value() < item2.get_drop_value():
        return -1
    elif item1.get_drop_value() > item2.get_drop_value():
        return 1
    else:
        return 0


def compare_by_level(item1, item2):
    if item1.level < item2.level:
        return -1
    elif item1.level > item2.level:
        return 1
    else:
        return 0


def main():
    global cursor
    conn = pypyodbc.win_connect_mdb('l2.mdb')
    cursor = conn.cursor()

    mobs = []
    cursor.execute('''SELECT monsters.id, npcnames.name, monsters.level, exp FROM monsters'''\
                   + ''' INNER JOIN npcnames ON monsters.id = npcnames.id'''\
                +''' WHERE monsters.npc = 0 AND monsters.show = True AND '''\
                +'''monsters.level >= ''' + str(SELECT_MIN_LEVEL) + ''' AND monsters.level <=  '''\
                   + str(SELECT_MAX_LEVEL) +';')
    for row in cursor.fetchall():
        mob = Mob(row)
        mobs.append(mob)
    mobs = [value for value in mobs if value.get_drop_value() >= MINIMUM_DROP_VALUE\
        and value.get_drop_value() <= MAXIMUM_DROP_VALUE]
    if SORT_TYPE == SORT_BY_LEVEL:
        mobs.sort(cmp=compare_by_level)
    elif SORT_TYPE == SORT_BY_DROP:
        mobs.sort(cmp=compare_by_drop)

    for mob in mobs:
        print(mob.level, mob.name, int(mob.get_drop_value()))

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()