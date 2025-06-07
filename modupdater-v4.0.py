# ============== Import libs Python 3.8 ===============
import os
import glob
import re
import ctypes.wintypes
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import logging
import argparse
import datetime

# @Author: FirePrince
# @Revision: 2025/06/07
# @Helper-script - creating change-catalogue: https://github.com/F1r3Pr1nc3/Stellaris-Mod-Updater/stellaris_diff_scanner.py
# @Forum: https://forum.paradoxplaza.com/forum/threads/1491289/
# @Git: https://github.com/F1r3Pr1nc3/Stellaris-Mod-Updater
# @TODO: replace in *.YML ?
# @TODO: extended support The Merger of Rules ?

ACTUAL_STELLARIS_VERSION_FLOAT = "4.0"  #  Should be number string
FULL_STELLARIS_VERSION = ACTUAL_STELLARIS_VERSION_FLOAT + '.15' # @last supported sub-version
# Default values
mod_path = "" # os.path.dirname(os.getcwd())
only_warning = 0
only_actual = 0
code_cosmetic = 1
also_old = 0
debug_mode = 0  # without writing file=log_file
mergerofrules = 0 # Forced support for compatibility with The Merger of Rules (MoR)
keep_default_country_trigger = 0
mod_outpath = ""  # if you don't want to overwrite the original
log_file = "modupdater.log"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Stellaris Mod Updater v4.0 script by FirePrince.\n",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-w', '--only_warning', action='store_true',
                        help='Enable only_warning mode (implies code_cosmetic = False)')
    parser.add_argument('-c', '--code_cosmetic', action='store_true',
                        help='Enable code_cosmetic mode (only if only_warning is False)')
    parser.add_argument('-a', '--only_actual', action='store_true',
                        help='Check only the latest version')
    parser.add_argument('-o', '--also_old', action='store_true',
                        help='Include support for pre-2.3 versions (beta)')
    parser.add_argument('-d', '--debug_mode', action='store_true',
                        help='Enable debug mode for development prints')
    parser.add_argument('-m', '--mergerofrules', action='store_true',
                        help='Forced support for compatibility with The Merger of Rules (MoR)')
    parser.add_argument('-k', '--keep_default_country_trigger', action='store_true',
                        help='Keep default country trigger')
    parser.add_argument('-ut', '--ACTUAL_STELLARIS_VERSION_FLOAT', type=str, default="4.0",
                        help='Specify the version number to update only, e.g., 3.7')
    parser.add_argument('-input', '--mod_path', type=str, default="",
                        help='Path to the mod directory')
    parser.add_argument('-output', '--mod_outpath', type=str, default="",
                        help='(Optional) Output path for the updated mod')

    return parser.parse_args()

# Process boolean parameters
def setBoolean(s):
    s = bool(s)

# if not sys.version_info.major == 3 and sys.version_info.minor >= 6:
#   print("Python 3.6 or higher is required.")
#   print("You are using Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
#   sys.exit(1)

VANILLA_ETHICS = r"pacifist|militarist|materialist|spiritualist|egalitarian|authoritarian|xenophile|xenophobe"
VANILLA_PREFIXES = r"any|every|random|count|ordered"
PLANET_MODIFIER = r"jobs|housing|amenities"
RESOURCE_ITEMS = r"energy|unity|food|minerals|influence|alloys|consumer_goods|exotic_gases|volatile_motes|rare_crystals|sr_living_metal|sr_dark_matter|sr_zro|(?:physics|society|engineering(?:_research))"
NO_TRIGGER_FOLDER = re.compile(r"^([^_]+)(_(?!trigger)[^/_]+|[^_]*$)(?(2)/([^_]+)_[^/_]+$)?")  # 2lvl, only 1lvl folder: ^([^_]+)(_(?!trigger)[^_]+|[^_]*)$ only
EFFECT_FOLDERS = {
    "events",
    "common/agendas",
    "common/anomalies",
    "common/ascension_perks",
    "common/buildings",
    "common/council_agendas",
    "common/civics",
    "common/colony_types",
    "common/component_templates",
    "common/decisions",
    "common/deposits",
    # "common/fallen_empires",
    "common/governments",
    "common/inline_scripts",
    "common/megastructures",
    "common/policies",
    "common/pop_faction_types",
    "common/relics",
    "common/scripted_effects",
    "common/solar_system_initializers",
    "common/species_classes",
    "common/starbase_buildings",
    "common/starbase_modules",
    "common/technology",
    "common/traditions",
    "common/traits",
}

def multiply_by_hundred(m):
    "Multiply regexp str integer by hundred"
    return f"{m.group(1)} {int(m.group(2))*100}"

# def multiply_by_hundred_float(m):
#     return f"{m.group(1)} {int(float(m.group(2))*100)}"

# TODO !? # SUPPORT name="~~Scripted Trigger Undercoat" id="2868680633" dropped due performance reasons
# 00_undercoat_triggers.txt
# undercoat_triggers = {
#   r"\bhas_origin = origin_fear_of_the_dark": "is_fear_of_the_dark_empire = yes",
#   r"\bhas_valid_civic = civic_warrior_culture": "has_warrior_culture = yes",
#   r"\bhas_valid_civic = civic_efficient_bureaucracy": "has_efficient_bureaucracy = yes",
#   r"\bhas_valid_civic = civic_byzantine_bureaucracy": "has_byzantine_bureaucracy = yes",
#   r"\bhas_civic = civic_exalted_priesthood": "has_exalted_priesthood = { allow_invalid = yes }",
# }
# targetsR = [] # Format: tuple is with folder (folder, regexp/list); list is with a specific message [regexp, msg]
# targets3 = {}
# targets4 = {}

actuallyTargets = {
    "targetsR": [],  # Removed syntax # This are only warnings, commands which cannot be easily replaced.
    "targets3": {},  # Simple syntax (only one-liner)
    "targets4": {},  # Multiline syntax # key (pre match without group or one group): arr (search, replace) or str (if no group or one group) # re flags=re.I|re.M|re.A
}

# TODO
# Loc yml job replacement

v4_0 = {
    # Used list_traits_diff.py script for changed traits
    "targetsR": [
        [r"\b(?:random|any)_pop\b", "REMOVED in v4.0: use any_owned_pop_group/any_species_pop_group"],
        # [r"\bclear_pop_category\b", "REMOVED in v4.0"],
        [r"\bcreate_half_species\b", "REMOVED in v4.0"],
        # [r"\bevery_galaxy_pop\b", "REMOVED in v4.0: use every_galaxy_species"], Too rare used
        # [r"\b(%s)_pop\b" % VANILLA_PREFIXES, "REMOVED in v4.0"],
        [r"\bremove_last_built_(building|district)\b", "REMOVED in v4.0"],
        [r"\breset_decline\b", "REMOVED in v4.0"],
        [r"\bcan_work_job\b", "REMOVED in v4.0"],
        # [r"\bcount_owned_pops\b", "REMOVED in v4.0"],
        [r"\bhas_collected_system_trade_value\b", "REMOVED in v4.0"],
        [r"\bhas_system_trade_value\b", "REMOVED in v4.0"],
        [r"\bhas_trade_route\b", "REMOVED in v4.0"],
        [r"\bnum_trade_routes\b", "REMOVED in v4.0"],
        [r"\btrade_income\b", "REMOVED in v4.0"],
        [r"\btrade_intercepted_(value|percentage)\b", "REMOVED in v4.0"],
        [r"\btrade_protected_(value|percentage)\b", "REMOVED in v4.0"],
        [r"\bstarbase_trade_protection(_range)?_add\b", "REMOVED in v4.0"],
        [r"\btrade_route_value\b", "REMOVED in v4.0"],
        [r"\btrading_value\b", "REMOVED in v4.0"],
        [r"\bhas_uncollected_system_trade_value\b", "REMOVED in v4.0"],
        [r"\bis_half_species\b", "REMOVED in v4.0"],
        [r"\bplanet_telepaths_unity_produces_add\b", "REMOVED in v4.0"],
        [r"\bleader_trait_expeditionist\b", "REMOVED in v4.0"],
        # Modifier
        [r"\bbranch_office_value\b", "REMOVED in v4.0"],
        [r"\bdiplo_fed_xpboost\b", "REMOVED in v4.0"],
        [r"\bhabitat_district_jobs_add\b", "REMOVED in v4.0"],
        [r"\bhabitat_districts_building_slots_add\b", "REMOVED in v4.0"],
        [r"\bjob_preacher_trade_value_add\b", "REMOVED in v4.0"],
        [r"\bmanifesti_uslurp_mod\b", "REMOVED in v4.0"],
        # Scripted Effects
        [r"\barc_furnace_update_orbital_effect\b", "REMOVED in v4.0"],
        [r"\bassimilation_effect\b", "REMOVED in v4.0, compare set_assimilation_counter_variable"],
        # [r"\bmake_pop_zombie\b", "REMOVED in v4.0"],
        [r"\bpop_diverge_ethic\b", "REMOVED in v4.0"],
        [r"\bsurveyor_update_orbital_effect\b", "REMOVED in v4.0"],
        [r"\btoxic_knights_order_habitat_setup\b", "REMOVED in v4.0"],
        [r"\bupdate_habitat_orbital_effect\b", "REMOVED in v4.0"],
        [r"\bwipe_pop_ethos\b", "REMOVED in v4.0"],
        # Scripted Trigger
        [r"\bbuildings_unemployed\b", "REMOVED in v4.0"],
        [r"\bcan_assemble_budding_pop\b", "REMOVED in v4.0"],
        [r"\bcan_assemble_clone_soldier_pop\b", "REMOVED in v4.0"],
        [r"\bcan_assemble_tiyanki_pop\b", "REMOVED in v4.0"],
        [r"\benigmatic_modifier_jobs\b", "REMOVED in v4.0"],
        # [r"\bhas_any_industry_district\b", "REMOVED in v4.0"],
        # [r"\bhas_any_mining_district\b", "REMOVED in v4.0"],
        [r"\bhas_refinery_designation\b", "REMOVED in v4.0"],
        [r"\bhas_research_job\b", "REMOVED in v4.0"],
        [r"\bjobs_any_research\b", "REMOVED in v4.0"],
        [r"\btrait_(advanced_(?:budding|gaseous_byproducts|scintillating|volatile_excretions|phototrophic)|(?:advanced|harvested|lithoid)_radiotrophic)\b", "REMOVED in v4.0"],
        # Events
        [r"\bid = (?:action\.(?:202[01]|6(?:4|5[05]?))|ancrel\.1000[4-9]|first_contact\.106[01]|game_start\.6[25]|megastructures\.(?:1(?:00|1[05]?|[23]0)|50)|pop\.(?:1[0-4]|[235-9])|advisor\.26|cyber\.7|distar\.305|enclave\.2015|fedev\.655|origin\.5081|subject\.2145)\b", "EVENT REMOVED in v4.0"],
        # [r"\bis_unemployed\b", "REMOVED in v4.0"],
        # [r"\bpop_produces_resource\b", "REMOVED in v4.0"],
        [r"\bunemploy_pop\b", "REMOVED in v4.0, use transfer_pop_amount"],
        [r"\btech_(?:leviathan|lithoid|plantoid)_transgenesis\b", "REMOVED in v4.0, use something like can_add_or_remove_leviathan_traits"], # The only techs

    ],
    "targets3": {
        r"\b((?:%s)_species_pop)\b" % VANILLA_PREFIXES: r"\1_group",
        r"\b((?:leader_)?trait_)(adaptable|aggressive|agrarian_upbringing|architectural_interest|army_veteran|bureaucrat|butcher|cautious|eager|engineer|enlister|environmental_engineer|defence_engineer|politician|resilient|restrained|retired_fleet_officer|ruler_fertility_preacher|shipwright|skirmisher|trickster|unyielding)_2":
            r"\1\2",
        r"\b((?:leader_)?trait_)(annihilator|archaeo_specialization|armada_logistician|artillerist|artillery_specialization|border_guard|carrier_specialization|commanding_presence|conscripter|consul_general|corsair|crew_trainer|crusader|demolisher|dreaded|frontier_spirit|gale_speed|guardian|gunship_specialization|hardy|heavy_hitter|home_guard|interrogator|intimidator|juryrigger|martinet|observant|overseer|reinforcer|rocketry_specialization|ruler_fortifier|ruler_from_the_ranks|ruler_military_pioneer|ruler_recruiter|scout|shadow_broker|shipbreaker|slippery|surgical_bombardment|tuner|warden|wrecker)_3":
            r"\1\2_2",
        r"^[^#]*?(\s+)country_event = \{\s+id = first_contact.1060[^{}#]+\}": r"\1if = {\n\1\tlimit = { very_first_contact_paragon = yes }\n\1\tset_country_flag = first_contact_protocol_event_happened\n\1}",
        r"\bplanet_storm_dancers\b": "planet_entertainers",
        r"\bhas_any_industry_district\b": (NO_TRIGGER_FOLDER, "has_any_industry_zone"),
        r"\bhas_any_mining_district\b": (NO_TRIGGER_FOLDER, "has_any_capped_planet_mining_district"),
        r"\b(?:add|remove)_leader_traits_after_modification\b": "update_leader_after_modification",
        r"\bgenerate_servitor_assmiliator_secondary_pops\b": "generate_civic_secondary_pops",
        r"\bmake_pop_zombie\b": "create_zombie_pop_group",
        r"\btrait_frozen_planet_preference\b": "trait_cold_planet_preference",
        r"\btrait_cyborg_climate_adjustment_frozen\b": "trait_cyborg_climate_adjustment_cold",
        r"\b(count_owned_pop)\b": r"\1_amount",
        r"\b(random_owned_pop)\b": r"weighted_\1_group", # Weighted on the popgroup size
        r"\b((?:any|every|ordered)_owned_pop) =": r"\1_group =",
        r"\bnum_(sapient_pop|pop)s\s*([<=>]+)\s*(\d+)": lambda m: f"{m.group(1)}_amount {m.group(2)} {int(m.group(3))*100}",
        r"\b(min_pops_to_kill_pop\s*[<=>]+)\s*([1-9]\d?)\b": ("common/bombardment_stances", multiply_by_hundred),
        r"\b((?:VOIDWORMS_MAXIMUM_POPS_TO_KILL\w*?|POP_FACTION_MIN_POTENTIAL_MEMBERS|MAX_CARRYING_CAPACIT|RESETTLE_UNEMPLOYED_BASE_RATE|\w+_BUILD_CAP|AI_SLAVE_MARKET_SELL_LIMIT|SLAVE_BUY_UNEMPLOYMENT_THRESHOLD|SLAVE_SELL_UNEMPLOYMENT_THRESHOLD|SLAVE_SELL_MIN_POPS) =)\s*([1-9]\d?)\b":
            ("common/defines", multiply_by_hundred),
        r"^(\s+[^#]*?)\bbase_cap_amount\b": ("common/buildings", r"\1planet_limit"),
        r"\buse_ship_kill_target\b": ("common/component_templates", "use_ship_main_target"),
        r"^(\s+)(potential_crossbreeding_chance =)": ("common/traits", r"\1# \2"),
        r"^(\s+)(ship_piracy_suppression_add =)": ("common/ship_sizes", r"\1# \2"),
        r"\s+standard_trade_routes_module = {}": ("common/country_types", ""),
        r"\s+collects_trade = (yes|no)": ("common/starbase_levels", ""),
        r"\bclothes_texture_index = \d+": (["common/pop_jobs","common/pop_categories"], ""),
        r"^(\s+)(ignores_favorite =)": ("common/pop_jobs", r"\1# \2"),
        r"\bnum_(sapient_pop|pop)s\b":  r"\1_amount",
        r"\bclear_pop_category = yes": "",
        r"\bkill_pop = yes": "kill_single_pop = yes", # "kill_pop_group = { pop_group = this amount = 100 }"
        # r"\bkill_pop = yes": "kill_all_pop = yes", # "kill_pop_group = { pop_group = this percentage = 1 }"
        r"\bpop_has_(ethic|trait|happiness)\b":  r"pop_group_has_\1",
        r"\bpop_percentage\b": "pop_amount_percentage",
        r"\bhas_skill\b": "has_total_skill",
        r"\bhas_level\b": "has_base_skill",
        r"\bhas_job\b": "has_job_type",
        # r"\bis_robot_pop\b": "is_robot_pop_group", needs to be concrete
        r"\bcategory = pop\b": "category = pop_group",
        r"\b(owner_(main_)?)?species = { has_trait = trait_psionic }\b": "can_talk_to_prethoryn = yes",
        r"^(\s+)pop_change_ethic = ([\d\w\.:]+)\b":  r"\1pop_group_transfer_ethic = {\n\1\tPOP_GROUP = this\n\1\tETHOS = \2\n\1\tPERCENTAGE = 1\n\1}", # AMOUNT = 100
        r"\b(create_pop = \{ species = [\d\w\.:]+ )count( = \d+)":  r"\1size\2", # Just cheap pre-fix
        r"\b(set|set_timed|has|remove)_pop_flag\b":  r"\1_pop_group_flag",
        r"\bhas_active_tradition = tr_genetics_finish_extra_traits\b": "can_harvest_dna = yes",
        r"\bis_pop_category = specialist\b": "is_specialist_category = yes",
        r"\bguardian_warden\b": "guardian_opus_sentinel",
        r"\bbuilding_clinic\b": "building_medical_2",
        # r"\boffspring_drone\b": "spawning_drone",
        r"\bplanet_priests\b": "planet_bureaucrats",
        r"\bjob_(?:priest|death_priest)_add\b": "job_bureaucrat_add", # |preacher|steward|manager|haruspex|mortal_initiate
        r"\bjob_archaeoengineers_add\b": "job_biologist_add",
        r"\bjob_archaeo_unit_add\b": "job_bath_attendant_machine_add",
        r"(\s+)job_(?:calculator|brain_drone)_add = (-?[1-9])\b\n?": lambda m:
            f"{m.group(1)}job_calculator_physicist_add = {int(m.group(2))*50}\n{m.group(1)}job_calculator_biologist_add = {int(m.group(2))*20}\n{m.group(1)}job_calculator_engineer_add = {int(m.group(2))*30}\n",
        r"\bpop_event\b": "pop_group_event",
        ## Modifier
        r"\bpop_habitability\b": "pop_low_habitability",
        r"\bpop_growth_from_immigration\b": "planet_resettlement_unemployed_mult",
        r"\bplanet_immigration_pull_(mult|add) = (-?[\d.]+)": lambda m: f"planet_resettlement_unemployed_destination_{m.group(1)} = {float(m.group(2))*2}",
        r"\btrade_value_(mult|add)\b": r"planet_jobs_trade_produces_\1",
        r"pop_modifier\b": "pop_group_modifier",
        r"\bpop_growth_speed\b": "founder_species_growth_mult", # "BIOLOGICAL_bonus_pop_growth_mult", or logistic_growth_mult
        r"pop_growth_speed_reduction = -?(\d)": r"logistic_growth_mult = -\1",
        r"\bpop_job_trade_(mult|add)\b": r"trader_jobs_bonus_workforce_\1",
        r"\bpop_demotion_time_(mult|add)\b": r"pop_unemployment_demotion_time_\1",
        r"\bplanet_(?:priests|administrators)_(\w+_(?:mult|add))\s+":  r"planet_bureaucrats_\1 ",
        r"\bplanet_pop_assembly_organic_(mult|add)\b": r"bonus_pop_growth_\1",
        r"\bplanet_jobs_robotic_produces_(mult|add)\b": r"pop_bonus_workforce_\1",
        r"\bplanet_jobs_robot_worker_produces_(mult|add)\b": r"worker_and_simple_drone_cat_bonus_workforce_\1",
        r"\bplanet_researchers_society_research_produces_(mult|add)\b": r"planet_doctors_society_research_produces_\1",
        # Modifier trigger
        r"\b((?:num_unemployed|free_(?:%s))\s*[<=>]+)\s*(-?[1-9]\d?)\b" % PLANET_MODIFIER: multiply_by_hundred,
        # Modifier effect
        r"\b((?:planet_(?:%s|amenities_no_happiness)|job_(?!calculator_biologist|calculator_physicist|calculator_engineer|soldier_stability|researcher_naval_cap)\w+?)_add =)\s*(-?[1-9]\d?)\b" % PLANET_MODIFIER: multiply_by_hundred,
        # r"\b((?:planet_(?:%s|amenities_no_happiness)|job_(?!calculator)\w+?(?!stability|cap|value))_add =)\s*(-?(?:\d+\.\d+|\d\d?\b))" % PLANET_MODIFIER: multiply_by_hundred, # |calculator_(?:biologist|physicist|engineer)
    },
    "targets4": {
        r"\bevery_owned_pop_group = {\s+kill_single_pop = yes\s+\}": "every_owned_pop_group = { kill_all_pop = yes }",
        r"\bcreate_pop = \{(\s*)(?:species|count) = [\d\w\.:]+(?:\1ethos = (?:[\d\w\.:]+|\{\s*ethic = \"?\w+\"?(?:\s+ethic = \"?\w+\"?)?\s*\})|\s*)\1(?:species|count) = [\d\w\.:]+\s*\}":
            [r"\bcount( = \d+)", r"size\1"],
        r"(\s+)random_owned_pop = \{\s+resettle_pop = \{\s+[^{}#]+\s*\}\s+\}": [
            r"(\s+)random_owned_pop = \{\s+resettle_pop = \{\s+pop = ([\d\w\.:]+)\s*planet = ([\d\w\.:]+)\s+\}",
            r"\1resettle_pop_group = {\1\tPOP_GROUP = \2\1\tPLANET = \3\1\tPERCENTAGE = 1"
        ],
        r"\bpop_produces_resource = \{\s+[^{}#]+\}": [r"\(bpop_produces_resource) = \{\s+(type = \w+)\s+(amount\s*[<=>]+\s*[^{}\s]+)\s+\}", r"# \1= { \2 \3 }"], # Comment out
        r"\bcount_owned_pop_amount = \{\s+(?:limit = \{[^#]+?\}\s+)?count\s*[<=>]+\s*[1-9]\d?\s": [r"\b(count\s*[<=>]+)\s*(\d+)", multiply_by_hundred],
        r"\bnum_assigned_jobs = \{\s*(?:job = [^{}#\s]+\s+)?value\s*[<=>]+\s*[1-9]\d?\s": [r"\b(value\s*[<=>]+)\s*(\d+)", multiply_by_hundred],
        r"\bwhile = \{\s*count = \d+\s+create_pop = \{\s*species = [\d\w\.:]+(?:\s*ethos = (?:[\d\w\.:]+|\{\s*ethic = \w+(?:\s+ethic = \w+)?\s*\})|\s*)\s*\}\s*\}": [ # TODO count with vars needs to be tested
            r"while = \{\s*count = (\d+)\s+create_pop = \{\s*(species = [\d\w\.:]+)\s+(ethos = (?:[\d\w\.:]+|\{\s*ethic = \w+(?:\s+ethic = \w+)?\s*\})|\s*)\s*\}\s*\}",
            r"create_pop = { \2 size = \1\3 }"],
        r"\ballowed_peace_offers = \{\s+(?:(?:status_quo|surrender|demand_surrender)\s+){1,3}\s*\}": [
            r"allowed_peace_offers = \{\s+(status_quo|surrender|demand_surrender)\s*(status_quo|surrender|demand_surrender)?\s*(status_quo|surrender|demand_surrender)?\s*\}",
            ("common/war_goals", lambda p: ""
                if p.group(3)
                else
                    "forbidden_peace_offers = { " + (
                        {
                            "status_quo": 'surrender = "" demand_surrender = ""',
                            "surrender": 'status_quo = "" demand_surrender = ""',
                            "demand_surrender": 'status_quo = "" surrender = ""'
                        }[p.group(1)]
                        if not p.group(2)
                        else
                            'status_quo = ""'
                            if p.group(1) != "status_quo" and p.group(2) != "status_quo"
                            else
                                'surrender = ""'
                                if p.group(1) != "surrender" and p.group(2) != "surrender"
                                else 'demand_surrender = ""'
                    ) + " }"
            )],
        r"\n(?:\t(?:condition_string|building_icon|icon) = \w+\n){1,3}": [r"(\t(?:condition_string|building_icon|icon) = \w+\n)\s*?(\t(?:condition_string|building_icon|icon) = \w+\n)?\s*?(\t(?:condition_string|building_icon|icon) = \w+\n)?", ("common/pop_jobs", lambda m:
                '\tswappable_data = {\n\t\tdefault = {\n\t\t'+m.group(1)+
                ('\t\t'+m.group(2) if m.group(2) else '')+
                ('\t\t'+m.group(3) if m.group(3) else '')+
                '\t\t}\n\t}\n'
            )],
    },
}

v3_13 = {
    "targetsR": [
        # [r"\bhas_authority\b", "Replaced in v3.13 with scripted trigger"]
        [r"^\s*?[^#]+\s+\b(?:%s)_(?:system|galaxy_(?:fleet|planet|pop|species))\b" % "every|count|ordered", "global command"] # VANILLA_PREFIXES
    ],
    "targets3": {
        r"\bhas_authority = (\"?)auth_(imperial|democratic|oligarchic|dictatorial)\1\b":  (NO_TRIGGER_FOLDER, r"is_\2_authority = yes"),
    },
    "targets4": {
        # SEE README_NAME_LISTS.txt
        r"\bruler_names = \{\s*default = \{\s*full_names = \{": ("common/name_lists", "regnal_full_names = {"),
        r"\b(?:pop_percentage|count_owned_pop) = \{\n?\s+(?:(?:percentage|count)\s*[<=>]+\s*-?[\d.]+)?\s*limit = \{\s+has_ethic\b":
            [r"\{\n?(\s+(?:percentage|count)\s*[<=>]+\s*-?[\d.]+)?(\s*limit = \{\s+)", r"{\n\1\2pop_"],
        r"\bany_owned_pop = \{\s*is_enslaved = (?:yes|no)\s*\}": [
            r"any_owned_pop = \{\s*is_enslaved = (yes|no)\s*",
            lambda p: "count_enslaved_species = { count " + {"yes": ">", "no": "="}[p.group(1)] + " 0 "
        ],
        r"\s(?:\bNO[RT]|\bOR) = \{\s*(?:pop_has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2}\}": [
            r"(N)?O[RT] = \{\s*(?:pop_has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2}\}", (NO_TRIGGER_FOLDER,
            lambda p: "is_robot_pop = " + ("no" if p.group(1) else "yes")
        )],
        r"\bany_owned_pop = \{\s*is_robot(?:_pop|ic) = (?:yes|no)\s*\}": [
            r"any_owned_pop = \{\s*is_robot(?:_pop|ic)  = (yes|no)\s*\}", (NO_TRIGGER_FOLDER, r"any_owned_species = { is_robotic = \1 }")],
        r"\bset_faction_hostility = \{\s*(?:target = [\d\w\.:]+)?(?:\s+set_(?:hostile|neutral|friendly) = (?:yes|no)){3}\s*(?:target = [\d\w\.:]+)?\s*\}": [
            r"\s+(?:\w+ = no\s+){0,2}(set_(?:hostile|neutral|friendly) = yes)\s*?(?:\w+ = no\s+){0,2}\s*(target = [\d\w\.:]+)?\s*\}",
            lambda p: " " + p.group(1) + " " + (p.group(2) + " }" if p.group(2) else "}")],
        r"\s(?:\bNO[RT]|\bOR) = \{\s*(?:has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2}\}": [
            r"\b(NO[RT]|OR) = \{\s*(?:has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2}\}", (NO_TRIGGER_FOLDER,
            lambda p: "is_robotic = " + ("yes" if p.group(1) and p.group(1) == "OR" else "no")
        )],
        # Just works in species scope but is_species_class works also in country scope?
        # r"\s(?:\bNO[RT]|\bOR) = \{\s*(?:(?:is_species_class = (?:ROBOT|MACHINE)\s*?){2}|(?:has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2})\}": [
        #   r"\b(NO[RT]|OR) = \{\s*(?:(?:is_species_class = (?:ROBOT|MACHINE)\s*?){2}|(?:has_trait = \"?trait_(?:mechanical|machine_unit)\"?\s*?){2})\}", (NO_TRIGGER_FOLDER,
        #   lambda p: f"is_robotic = {'yes' if p.group(1) == 'OR' else 'no'}"
        # )],
        # Outdated count -> size on v4.0
        # r"\bwhile = \{\s*count = \d+\s+create_pop = \{\s*species = [\d\w\.:]+(?:\s*ethos = (?:[\d\w\.:]+|\{\s*ethic = \w+(?:\s+ethic = \w+)?\s*\})|\s*)\s*\}\s*\}": [ # TODO count with vars needs to be tested
        #   r"while = \{\s*(count = \d+)\s+create_pop = \{\s*(species = [\d\w\.:]+)(\s*ethos = (?:[\d\w\.:]+|\{\s*ethic = \w+(?:\s+ethic = \w+)?\s*\})|\s*)\s*\}\s*\}",
        #   r"create_pop = { \2 \1\3 }"],
    },
}

# """== 3.12 Quick stats ==
# Any portrait definition in species_classes is moved to new portrait_sets database
# Removed obsolete is_researching_area and research_leader triggers.
# is_individual_machine = { founder_species = { is_archetype = MACHINE } is_gestalt = no }
# """
v3_12 = {
    "targetsR": [
        [r"\bgenerate_cyborg_extra_treats\b", "Removed in v3.12, added in v3.6"],
        [r"\bstations_produces_mult\b", "Removed in v3.12,"],
        # [r"modifier = crucible_colony\b", "Removed in v3.12,"],
        [r"\bactivate_crisis_progression = yes\b", "Since v.3.12 needs a crisis path"],
        [r"\bresearch_leader\b", ("common/technology", "Leads to CTD in v3.12.3! Obsolete since v.3.8")]
    ],
    "targets3": {
        r"\bset_gestalt_node_protrait_effect\b": "set_gestalt_node_portrait_effect",
        r"(\w+modifier = )crucible_colony\b": r"\1gestation_colony",
        r"\bhas_synthethic_dawn = yes": 'host_has_dlc = "Synthetic Dawn Story Pack"',  # 'has_synthetic_dawn', enable it later for backward compat.
        r"\bhas_origin = origin_post_apocalyptic\b": (NO_TRIGGER_FOLDER, "is_apocalyptic_empire = yes", ),
        r"\bhas_origin = origin_subterranean\b": (NO_TRIGGER_FOLDER, "is_subterranean_empire = yes", ),
        r"\bhas_origin = origin_void_dwellers\b": (NO_TRIGGER_FOLDER, "has_void_dweller_origin = yes", ),
        r"\bhas_(?:valid_)?civic = civic_worker_coop\b": (NO_TRIGGER_FOLDER, "is_worker_coop_empire = yes"),
        r"\btr_cybernetics_assembly_standards\b": "tr_cybernetics_augmentation_overload",
        r"\btr_cybernetics_assimilator_crucible\b": "tr_cybernetics_assimilator_gestation",
        r"\btr_synthetics_synthetic_age\b": "tr_synthetics_transubstatiation_synthesis",
        r"\bactivate_crisis_progression = yes\b": "activate_crisis_progression = nemesis_path",
        r"\@faction_base_unity\b": "@faction_base_output",
        r"\bd_hab_nanites_1\b": "d_hab_nanites_3",
        r"^(\s+[^#]*?)has_country_flag = cyborg_empire\b": r"\1is_cyborg_empire = yes",
        r"\bis_(berserk_)?fallen_machine_empire\b": r"is_fallen_empire_\1machine",  # From 1.9
        r"\bgovernment_election_years_(add|mult)\b": r"election_term_years_\1",  # 3.12.3
    },
    "targets4": {
        r"\bOR = \{\s*(?:has_ascension_perk = ap_mind_over_matter\s+has_origin = origin_shroudwalker_apprentice|has_origin = origin_shroudwalker_apprentice\s+has_ascension_perk = ap_mind_over_matter)\s*\}": (NO_TRIGGER_FOLDER, "has_psionic_ascension = yes"),
        r"\s(?:\bNO[RT]|\bOR) = \{\s*(?:has_(?:valid_)?civic = \"?civic_death_cult(?:_corporate)?\"?\s*?){2}\}": [
            r"\b(NO[RT]|OR) = \{\s*(?:has_(?:valid_)?civic = \"?civic_death_cult(?:_corporate)?\"?\s*?){2}\}", (NO_TRIGGER_FOLDER,
            lambda p: "is_death_cult_empire = " + ("yes" if p.group(1) and p.group(1) == "OR" else "no")
        )],
        r"\bOR = \{\s*(?:has_ascension_perk = ap_synthetic_(?:evolution|age)\s+has_origin = origin_synthetic_fertility|has_origin = origin_synthetic_fertility\s+has_ascension_perk = ap_synthetic_(?:evolution|age))\s*\}": (
            NO_TRIGGER_FOLDER,
            "has_synthetic_ascension = yes",
        ),
        r"(\b(OR = \{\s+)?(?:is_artificial = yes\s+is_planet_class = pc_cosmogenesis_world|is_planet_class = pc_cosmogenesis_world\s+is_artificial = yes)(?(2)\s+\}))": r"is_artificial = yes",
    },
}
if code_cosmetic and not only_warning:
    v3_12["targets3"][r"\bhas_ascension_perk = ap_engineered_evolution\b"] = (NO_TRIGGER_FOLDER, "has_genetic_ascension = yes")
    v3_12["targets4"][
        r"(?:has_(?:valid_)?civic = civic_(?:hive_)?natural_design\s+?){2}"
    ] = (NO_TRIGGER_FOLDER, "is_natural_design_empire = yes")
    v3_12["targets4"][
        r"(?:has_origin = origin_cybernetic_creed\s+has_country_flag = cyber_creed_advanced_government|has_country_flag = cyber_creed_advanced_government\s+has_origin = origin_cybernetic_creed)"
    ] = (NO_TRIGGER_FOLDER, "is_cyber_creed_advanced_government = yes")
    v3_12["targets4"][
        r"(?:is_country_type = (?:(?:awakened_)?synth_queen(?:_storm)?\s*?)){3}"
    ] = (NO_TRIGGER_FOLDER, "is_synth_queen_country_type = yes")

# """== 3.11 Quick stats ==
# the effect 'give_breakthrough_tech_option_or_progress_effect' has been introduced
# the effect 'give_next_breakthrough_effect' has been introduced
# the trigger leader_lifespan has been introduced
# modifier ships_upkeep_mult could be replaced with ship_orbit_upkeep_mult
# the decision_prospect was removed
# Removed ...
# """
v3_11 = {
    "targetsR": [
        [
            r"\btech_(society|physics|engineering)_\d",
            "Removed in v3.11 after having their function made redundant",
        ],
        # [r"\bplanet_researchers_upkeep_mult", "Removed in v3.11"], ??
        [r"\bstation_uninhabitable_category", "Removed in v3.11"],
    ],
    "targets3": {
        r"\bgive_next_tech_society_option_effect = yes": "give_next_breakthrough_effect = { AREA = society }",
        # r"^(\s+[^#]*?)\bplanet_researchers_upkeep_mult = -?\d+\.?\d*": r'\1',
        # r'^(\s+[^#]*?)\b\"?tech_(?:society|physics|engineering)_\d\"?\b\s?': r'\1',
        r"\b(veteran_class_locked_trait|negative|subclass_trait|destiny_trait) = yes": (
            "common/traits",
            lambda p: "leader_trait_type = "
            + {
                "negative": "negative",
                "subclass_trait": "subclass",
                "destiny_trait": "destiny",
                "veteran_class_locked_trait": "veteran",
            }[p.group(1)],
        ),
        r"\badd_trait = leader_trait_(maniacal)": r"add_or_level_up_veteran_trait_effect = { TRAIT = leader_trait_\1 }",
    },
    "targets4": {
        r"\bany_country = \{[^{}#]*(?:position_on_last_resolution|is_galactic_community_member|is_part_of_galactic_council)": [
            r"any_country = (\{[^{}#]*(?:position_on_last_resolution|is_galactic_community_member|is_part_of_galactic_council))",
            r"any_galcom_member = \1",
        ],
        r"\s(?:every|random|count)_country = \{[^{}#]*limit = \{\s*(?:position_on_last_resolution|is_galactic_community_member|is_part_of_galactic_council)": [
            r"(\s(?:every|random|count))_country = (\{[^{}#]*limit = \{\s*(?:position_on_last_resolution|is_galactic_community_member|is_part_of_galactic_council))",
            r"\1_galcom_member = \2",
        ],
        r"\b(?:(?:is_planet_class = pc_(?:city|relic)\b|merg_is_(?:arcology|relic_world) = yes)\s*?){2}": (
            NO_TRIGGER_FOLDER,
            "is_urban_planet = yes",
        ),
    },
}
if code_cosmetic and not only_warning:
    v3_11["targets3"][r"^(\s+[^#]*?\btech_)((?:society|physics|engineering)_\d)"] = (
        lambda p: p.group(1)
        + {
            "society_1": "genome_mapping",
            "society_2": "colonization_3",
            "society_3": "colonization_4",
            "physics_1": "administrative_ai",
            "physics_2": "cryostasis_2",
            "physics_3": "combat_computers_3",
            "engineering_1": "powered_exoskeletons",
            "engineering_2": "space_mining_4",
            "engineering_3": "advanced_metallurgy_2",
        }[p.group(2)]
    )

# """== 3.10 Quick stats ==
# BTW: the modifier leader_age has been renamed to leader_lifespan_add, the trigger leader_lifespan has been introduced
# Removed paragon.5001
# leader sub-classes merged
# """
v3_10 = {
    "targetsR": [
        [r"\b\w+(skill|weight|agent|frontier)_governor\b",
            "Possibly renamed to '_official' in v3.10",
        ],
        # [r"\bnum_pops\b", "Can be possibly replaced with 'num_sapient_pops' in v3.10 (planet, country)"], # Not really recommended: needs to be more accurate
        [r"\btrait_ruler_(explorer|world_shaper)", "Removed in v3.10"],  # TODO
        [r"\bleader_trait_inspiring",
            "Removed in v3.10, possible replacing by leader_trait_crusader",
        ],  # TODO: needs to be more accurate
        [r"\s+kill_leader = \{ type", "Probably outdated since 3.10", ],  # TODO: needs to be more accurate
        [r"\bai_categories", (["common/traits"], "Replaced in v3.10 with 'inline_script'")],
        [r"\b(?:is_)?councilor_trait", (["common/traits"],
                            "Replaced in v3.10 with 'councilor_modifier' or 'force_councilor_trait = yes')")
        ],
        [r"\bselectable_weight = @class_trait_weight", (["common/traits"],
                            "Replaced in v3.10 with inline_script'"),
        ],
        [r"^\s+leader_class = \{\s*((?:admiral|general|governor)\s+){1,2}", (["common/traits", "common/governments/councilors"],
                            "Needs to be replaced with 'official' or 'commander' in v3.10"),
        ],
    ],
    "targets3": {
        r"\bcan_fill_specialist_job =": "can_fill_specialist_job_trigger =",
        r"\bleader_age = ": "leader_lifespan_add = ",
        r"^on_survey = \{": ("common/on_actions", "on_survey_planet = {"),
        r"councilor_trait = no\n?": ("common/traits", ""),
        r"^([^#]+?\w+gray_)governor\b": r"\1official",
        r'(class|CLASS) = ("?)governor\b': r"\1 = \2official",
        r'(class|CLASS) = ("?)(?:admiral|general)\b': r"\1 = \2commander",
        r'leader = ("?)(?:admiral|general)\b': (
            "common/special_projects",
            r"leader = \1commander",
        ),
        r"=\s*subclass_governor_(?:visionary|economist|pioneer)": "= subclass_official_governor",
        r"=\s*subclass_admiral_(?:tactician|aggressor|strategist)": "= subclass_commander_admiral",
        r"=\s*subclass_general_(?:invader|protector|marshall)": "= subclass_commander_general",
        # 4 sub-classes for each class
        r"=\s*subclass_scientist_analyst": "= subclass_scientist_governor",  # '= subclass_scientist_scholar', also new
        r"=\s*subclass_scientist_researcher": "= subclass_scientist_councilor",  # _explorer keeps same,
        r"\bcouncilor_gestalt_(governor|scientist|admiral|general)\b": lambda p: "councilor_gestalt_"
        + {
            "governor": "growth",
            "scientist": "cognitive",
            "admiral": "legion",
            "general": "regulatory",
        }[p.group(1)],
        r"^([^#]+?)\s+leader_trait_clone_(army|army_fertile)_admiral": r"\1 leader_trait_clone_\2_commander",
        r"^([^#]+?)\s+leader_trait_civil_engineer": r"\1 leader_trait_manufacturer",
        r"^([^#]+?)\s+leader_trait_scrapper_": r"\1 leader_trait_distribution_lines_",
        r"^([^#]+?)\s+leader_trait_urbanist_": r"\1 trait_ruler_architectural_sense_",
        r"^([^#]+?)\s+leader_trait_par_zealot(_\d)?\b": r"\1 leader_trait_crusader",
        r"^([^#]+?)\s+leader_trait_repair_crew\b": r"\1 leader_trait_brilliant_shipwright",
        r"^([^#]+?)\s+leader_trait_demolisher_destiny\b": r"\1 leader_trait_demolisher",
        r"^([^#]+?)\s+leader_trait_deep_space_explorer\b": r"\1 leader_trait_xeno_cataloger",
        r"^([^#]+?)\s+leader_trait_supreme_admiral\b": r"\1 leader_trait_military_overseer",
        r"^([^#]+?)\s+leader_trait_pilferer\b": r"\1 leader_trait_tzrynn_tithe",
        r"^([^#]+?)\s+leader_trait_kidnapper\b": r"\1 leader_trait_interrogator",
        r"^([^#]+?)\s+leader_trait_watchdog\b": r"\1 leader_trait_energy_weapon_specialist",
        r"^([^#]+?)\s+leader_trait_insightful\b": r"\1 leader_trait_academic_dig_site_expert",
        r"^([^#]+?)\s+leader_trait_experimenter\b": r"\1 leader_trait_juryrigger",
        r"^([^#]+?)\s+leader_trait_fanatic\b": r"\1 leader_trait_master_gunner",
        r"^([^#]+?)\s+leader_trait_glory_seeker": r"\1 leader_trait_butcher",
        r"^([^#]+?)\s+leader_trait_army_logistician(_\d)?\b": r"\1 leader_trait_energy_weapon_specialist",
        r"^([^#]+?)\s+leader_trait_fotd_admiral\b": r"\1 leader_trait_fotd_commander",
        # r'=\s*leader_trait_mining_focus\b': '= leader_trait_private_mines_2',
        r"add_modifier = \{ modifier = space_storm \}": "create_space_storm = yes",
        r"\bassist_research_mult = ([-\d.]+)\b": lambda p: "planet_researchers_produces_mult = "
        + str(round(int(p.group(1)) * 0.4, 2)),
        r"remove_modifier = space_storm": "destroy_space_storm = yes",
        r'(\s)num_pops\b': (["common/buildings", "common/decisions", "common/colony_types"], r'\1num_sapient_pops'), # WARNING: only on planet country (num_pops also pop_faction sector)
        r"^(\s*)(valid_for_all_(?:ethics|origins)\b.*)": (
            "common/traits",
            r"\1# \2 removed in v3.10",
        ),
        r"\sleader_class = \{\s*((?:(?:admiral|general|governor|scientist)\s+){2,4})": (
            ["common/traits", "common/governments/councilors"],
            lambda p: (
                p.group(0)
                if not p.group(1)
                else "  leader_class = { "
                + re.sub(
                    r"(admiral|general|governor)",
                    lambda p2: (
                        p2.group(0)
                        if not p2.group(1)
                        else {
                            "governor": "official",
                            "admiral": "commander",
                            "general": "commander",
                        }[p2.group(1)]
                    ),
                    p.group(1),
                    count=1,
                    flags=re.M | re.A,
                )
            ),
        ),
    },
    "targets4": {
        r'\bleader_class = "?commander"?\s+leader_class = "?commander"?\b': "leader_class = commander",
        # r"^\s+leader_class = \{\s*((?:admiral|scientist|general|governor)\s+){1,4}": [r'(admiral|general|governor)', (["common/traits", "common/governments/councilors"], lambda p: {"governor": "official", "admiral": "commander", "general": "commander" }[p.group(1)])],
        r"(?:\s+has_modifier = (?:toxic_|frozen_)?terraforming_candidate){2,3}\s*": " is_terraforming_candidate = yes ",
    },
}

v3_9 = {
    "targetsR": [
        # [r"\bland_army\s", "Removed army parameter from v3.8 in v3.9:"],  # only from 3.8
        # [r"\bhabitat_0\s", "Removed in v3.9: replaceable with 'major_orbital'"],  # only from 3.8
        [r"\bdistrict_hab_cultural", "Removed in v3.9: replaceable with 'district_hab_housing'?"],
        [r"\bdistrict_hab_commercial", "Removed in v3.9: replaceable with 'district_hab_energy'?"],
        [r"\bcol_habitat_leisure", "Removed in v3.9"],
        [r"\bis_regular_empire_or_primitive\b", "Removed in v3.9.0 from 3.6: replaceable with OR = { is_regular_empire is_primitive = yes }?"],  # only from 3.8
        [r"\bis_space_critter_country_type\b", "Removed in v3.9.2: possible replaceable with 'is_non_hostile_to_wraith'?"],  # only from 3.8
    ],
    "targets3": {
        # r'\bhabitat_0\b': 'major_orbital', # 'habitat_central_complex',
        r"\bimperial_origin_start_spawn_effect =": "origin_spawn_system_effect =",
        r"\b(?:is_orbital_ring = no|has_starbase_size >= starbase_outpost)": "is_normal_starbase = yes",
        r"\b(?:is_normal_starbase = no|has_starbase_size >= orbital_ring_tier_1)": "is_orbital_ring = yes",
        # r'\bhas_starbase_size (>)=? starbase_outpost': lambda p: 'is_normal_starbase = yes',
        r"\bcan_see_in_list = (yes|no)": lambda p: "hide_leader = " + {"yes": "no", "no": "yes"}[p.group(1)],
        # r'\bis_roaming_space_critter_country_type = (yes|no)':  lambda p: {"yes": "", "no": "N"}[p.group(1)] + 'OR = {is_country_type = tiyanki is_country_type = amoeba is_country_type = amoeba_borderless }', # just temp beta
    },
    "targets4": {
        # spawn_habitat_cracker_effect includes remove_planet = yes cosmetic
    },
}
# Galactic Paragons
v3_8 = {
    "targetsR": [
        # [r"\bsector(?:\.| = \{ )leader\b", "Removed in v3.8: replaceable with planet?"],
        [r"\bclass = ruler\b", "Removed in v3.8: replaceable with ?"],
        [r"\bleader_of_faction = [^\s]+", "Removed in v3.8: replaceable with ?"],
        [r"\bhas_mandate = [^\s]+", "Removed in v3.8: replaceable with ?"],
        [r"\bpre_ruler_leader_class =", "Removed in v3.8: replaceable with ?"],
        [r"\bruler_skill_levels =", "Removed in v3.8: replaceable with ?"],
        # [r"\bhas_chosen_trait_ruler =", "Replaced in v3.8.3 with 'has_chosen_one_leader_trait'"],
        # [r"\bis_specialist_researcher =", "Replaced trigger 3.8: is_specialist_researcher_(society|engineering|physics)"], scripted trigger now
    ],
    "targets3": {
        r"\bsector(\.| = \{ )leader\b": r"sector\1sector_capital.leader",
        r"\bset_is_female = yes": "set_gender = female",
        r"\bcountry_command_limit_": "command_limit_",
        r"\s+trait = random_trait\b\s*": "",
        # r'\btrait = leader_trait_(\w+)\b': r'0 = leader_trait_\1', # not necessarily
        r"(\s)has_chosen_trait_ruler =": r"\1has_chosen_one_leader_trait =",  # scripted trigger
        r"\btype = ruler\b": "ruler = yes",  # kill_leader
        r"\b(add|has|remove)_ruler_trait\b": r"\1_trait",
        r"\bclass = ruler\b": "class = random_ruler",
        r"\bleader_trait_(?:admiral|general|governor|ruler|scientist)_(\w*(?:chosen|psionic|brainslug|synthetic|cyborg|erudite))\b": r"leader_trait_\1",
        r"\bleader_trait_(\w+)\b": lambda p: (
            p.group(0)
            if not p.group(1)
            or p.group(1)
            not in {
                "charismatic",
                "newboot",
                "flexible_programming",
                "rigid_programming",
                "general_mercenary_warrior",
                "demoralizer",
                "cataloger",
                "maintenance_loop",
                "unstable_code_base",
                "parts_cannibalizer",
                "erratic_morality_core",
                "trickster_fircon",
                "warbot_tinkerer",
                "ai_aided_design",
                "bulldozer",
                "analytical",
                "archaeologist_ancrel",
                "mindful",
                "mindfulness",
                "amplifier",
            }
            else "leader_trait_"
            + {
                "charismatic": "inspiring",
                "newboot": "eager",
                "flexible_programming": "adaptable",
                "rigid_programming": "stubborn",
                "general_mercenary_warrior": "mercenary_warrior",
                "demoralizer": "dreaded",
                # DLC negative removed?
                "cataloger": "xeno_cataloger",  # leader_trait_midas_touch
                "maintenance_loop": "fleet_logistician",
                "unstable_code_base": "nervous",
                "parts_cannibalizer": "army_logistician",
                "erratic_morality_core": "armchair_commander",
                "trickster_fircon": "trickster_2",
                "warbot_tinkerer": "army_veteran",
                "ai_aided_design": "retired_fleet_officer",
                "bulldozer": "environmental_engineer",
                "analytical": "intellectual",
                "archaeologist_ancrel": "archaeologist",  # collective_wisdom?
                "mindful": "insightful",
                "mindfulness": "bureaucrat",
                "amplifier": "bureaucrat",
            }[p.group(1)]
        ),
        r"([^#]*?)\blength = 0": ("common/edicts", r"\1length = -1"),
        r"([^#]*?)\badd_random_leader_trait = yes": (
            ["common/scripted_effects", "events"],
            r"\1add_trait = random_common",
        ),
        r"\s*[^#]*?\bleader_trait = (?:all|\{\s*\w+\s*\})\s*": ("common/traits", ""),
        r"(\s*[^#]*?)\bleader_class ?= ?\"?ruler\"?": (
            "prescripted_countries",
            r'\1leader_class="governor"',
        ),
        r"\bleader_class = ruler\b": "is_ruler = yes",
        r"\s*[^#]*?\bis_researching_area = \w+": "",
        # r"\s+traits = \{\s*\}\s*": "",
        r"\bmerg_is_standard_empire = (yes|no)": r"is_default_or_fallen = \1",  # v3.8 former merg_is_standard_empire Merger Rule now vanilla
    },
    "targets4": {
        r"\s+traits = \{\s*\}": "",
        r"(?:exists = sector\n?\s+)?\s*sector = \{\s+exists = leader\b": [
            r"(exists = sector\n?\s+)?(\s*sector = \{\s+exists = )leader\b",
            r"\1\2sector_capital.leader",
        ],
        # TODO Needs still WARNING anyway as it is not fully perfect replace yet
        r"(\bresearch_leader = \{\s+area = \w+\s+(\w+ = \{)?[^{}#]+(?(2)[^{}#]+\})\s+\})": [
            r"research_leader = \{\s+area = \w+\s+(\w+ = \{\s*?)?has_trait = \"?(\w+)\"?(?(1)[^{}#]+\})\s+\}",
            (
                "common/technology",
                lambda p: (
                    p.group(1)
                    + "has_trait_in_council = { TRAIT = "
                    + p.group(2)
                    + " } }"
                    if p.group(1) and p.group(2) and isinstance(p.group(2), str)
                    else "has_trait_in_council = { TRAIT = " + p.group(2) + " }"
                ),
            ),
        ],
        r"\b(?:OR|NO[RT]) = \{\s*is_(?:default_or_fallen|synthetic_empire) = yes\s*\}": [
            r"\b(OR|NO[RT]) = \{\s*is_(default_or_fallen|synthetic_empire) = yes\s*\}",
            lambda p: "is_"
            + p.group(2)
            + " = "
            + {"OR": "yes", "NO": "no"}[p.group(1)[0:2].upper()],
        ],
        # with is_country_type_with_subjects & without AFE but with is_fallen_empire
        r"\b(?:(?:(?:is_country_type = default|merg_is_default_empire = yes|is_country_type_with_subjects = yes)\s+is_fallen_empire = yes)|(?:is_fallen_empire = yes\s+(?:is_country_type = default|merg_is_default_empire = yes|is_country_type_with_subjects = yes)))\s+": [
            r"\b((?:is_country_type = default|merg_is_default_empire = yes|is_fallen_empire = yes|is_country_type_with_subjects = yes)(\s+)){2,}",
            (NO_TRIGGER_FOLDER, r"is_default_or_fallen = yes\2"),
        ],
        # r"\bspecies = \{ has_trait = trait_hive_mind \}": r'is_hive_species = yes',
        r"(\t?(?:species|pop) = \{\s+(?:limit = \{\s+)?(NOT = \{\s*)?has_trait = trait_hive_mind\s*\}(?(2)\s*\}))": [
            r"((\t?)(?:species|pop) = \{\s*?(limit = \{)?(\s+))(NOT = \{\s*)?has_trait = trait_hive_mind\s*\}((?(4)\s*\}))", (NO_TRIGGER_FOLDER,
            lambda p: p.group(2)
            + (
                p.group(1)
                if p.group(3)
                else ("" if p.group(2) and len(p.group(2)) > 0 else p.group(1))
            )
            + "is_hive_species = "
            + ("no" if p.group(5) else "yes")
            + (
                p.group(6)
                if (p.group(3) and p.group(6) or not p.group(2) or len(p.group(2)) == 0)
                else ""
            )),
        ],
    },
}
# """== 3.7 Quick stats ==
# All primitive effects/triggers/events renamed/removed.
# """
v3_7 = {
    "targetsR": [
        [r"\bid = primitive\.\d", "Removed in v3.7: replaceable with 'preftl.xx' event"],
        [r"\bremove_all_primitive_buildings =", "Removed in v3.7:"],
        [r"\buplift_planet_mod_clear =", "Removed in v3.7:"],
        [r"\bcreate_primitive_armies =", "Removed in v3.7: done via pop job now"],
    ],
    "targets3": {
        r'\bvariable_string = "([\w.:]+)"': r'variable_string = "[\1]"',  # set square brackets
        r"\bset_mia = yes": "set_mia = mia_return_home",
        r"\bset_primitive_age( =|_effect =)": r"set_pre_ftl_age\1",
        r"\bis_country_type = primitive": r"is_primitive = yes",
        r"\bcreate_primitive_(species|blockers) = yes": r"create_pre_ftl_\1 = yes",
        r"\bsetup_primitive_planet = yes": "setup_pre_ftl_planet = yes",
        r"\bremove_primitive_flags = yes": "remove_pre_ftl_flags = yes",
        r"\bnuke_primitives_(\w*?)effect =": r"nuke_pre_ftls_\1effect =",
        r"\bgenerate(\w*?)_primitives_on_planet =": r"generate\1_pre_ftls_on_planet =",
        r"\bcreate_(\w*?)primitive_empire =": r"create_\1pre_ftl_empire =",
        r"\bcreate_(hegemon|common_ground)_member_(\d) = yes": r"create_\1_member = { NUM = \2 }",
        r"_planet_flag = primitives_nuked_themselves": "_planet_flag = pre_ftls_nuked_themselves",
        r"sound = event_primitive_civilization": "sound = event_pre_ftl_civilization",
    },
    "targets4": {
        r"\bset_pre_ftl_age_effect = \{\s+primitive_age =": [
            "primitive_age =",
            "PRE_FTL_AGE =",
        ],
    },
}
v3_6 = {
    # - .lua replaced by .shader
    "targetsR": [
        [
            r"\bhas_ascension_perk = ap_transcendence\b",
            "Removed in v3.6: can be replaced with 'has_tradition = tr_psionics_finish'",
        ],
        [
            r"\bhas_ascension_perk = ap_evolutionary_mastery\b",
            "Removed in v3.6: can be replaced with 'has_tradition = tr_genetics_resequencing'",
        ],
        [
            r"\btech_genetic_resequencing\b",
            "Replaced in v3.6: with 'tr_genetics_resequencing'",
        ],
    ],
    "targets3": {
        r"\bpop_assembly_speed": "planet_pop_assembly_mult",
        r"\"%O%": ("common/name_lists", '"$ORD$'),
        r"\bis_ringworld =": (NO_TRIGGER_FOLDER, "has_ringworld_output_boost ="),
        r"\btoken = citizenship_assimilation\b": (
            "common/species_rights",
            "is_assimilation = yes",
        ),
        r"\bplanet_bureaucrats\b": ("common/pop_jobs", "planet_administrators"),
        r"\btoken = citizenship_full(?:_machine)?\b": (
            "common/species_rights",
            "is_full_citizenship = yes",
        ),
        r"\btoken = citizenship_slavery\b": (
            "common/species_rights",
            "is_slavery = yes",
        ),
        r"\btoken = citizenship_purge(?:_machine)?\b": (
            "common/species_rights",
            "is_purge = yes",
        ),
        r"\t\tsequential_name = ([^\s_]+_)(?:xx([^x\s_]+)_(?:ROM|ORD)|([^x\s_]+)xx_(?:ROM|SEQ))": (
            "common/name_lists",
            r"\t\tsequential_name = \1\2\3",
        ),
        r"\bhas_ascension_perk = ap_transcendence\b": "has_tradition = tr_psionics_finish",
        r"\bhas_ascension_perk = ap_evolutionary_mastery\b": "has_tradition = tr_genetics_resequencing",
        r"\bhas_technology = \"?tech_genetic_resequencing\"?\b": "has_tradition = tr_genetics_resequencing",
        r"\bcan_remove_beneficial_traits\b": "can_remove_beneficial_genetic_traits",
        r'\b(format|noun|adjective|prefix_format) = \"([^{}\n#\"]+)\"': ("common/random_names", r'\1 = "{\2}"'), # TODO extend
    },
    "targets4": {
        r"\bis_triggered_only = yes\s+trigger = \{\s+always = no": [r"(\s+)(trigger = \{\s+always = no)", ("events", r"\1is_test_event = yes\1\2")],
        r"slot = \"?(?:SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template = \"?AUTOCANNON_\d\"?": [
            r"(=\s*\"?(SMALL|MEDIUM|LARGE)\w+\d+\"?\s+template = )\"?(AUTOCANNON_\d)\"?",
            ("common/global_ship_designs", r'\1"\2_\3"'),
        ],
        r"\bhas_(?:population|colonization|migration)_control = \{\s+value =": [
            "value",
            "type",
        ],
        r"\sNOR = \{\s*(?:has_trait = trait_(?:latent_)?psionic\s+){2}\}": [
            r"\bNOR = \{\s*(has_trait = trait_(?:latent_)?psionic\s+){2}\}",
            (NO_TRIGGER_FOLDER, "has_psionic_species_trait = no"),
        ],
        r"\sOR = \{\s*(?:has_trait = trait_(?:latent_)?psionic\s+){2}\}": [
            r"\bOR = \{\s*(has_trait = trait_(?:latent_)?psionic\s+){2}\}",
            (NO_TRIGGER_FOLDER, "has_psionic_species_trait = yes"),
        ],
        # r"\s(?:OR = \{\s*(?:has_trait = trait_(?:latent_)?psionic\s+){2}\})": "has_psionic_species_trait = yes",)
    },
}
v3_5 = {
    "targetsR": [
        # [r"\b(%s)_bordering_country = \{" % VANILLA_PREFIXES, 'just use xyz_country_neighbor_to_system instead'],
        # [r"\b(restore|store)_galactic_community_leader_backup_data = ", 'now a scripted effect or just use store_country_backup_data instead']
    ],
    "targets3": {
        r"\b(%s)_bordering_country\b" % VANILLA_PREFIXES: r"\1_country_neighbor_to_system",
        r"\bcountry_(?!base_)(%s)_produces_add\b" % RESOURCE_ITEMS: r"country_base_\1_produces_add",
        r"\bhair( =)": ("prescripted_countries", r"attachment\1"),
        r"\bhair(_selector =)": ("gfx/portraits/portraits", r"attachment\1"),
        r"\bship_archeaological_site_clues_add =": "ship_archaeological_site_clues_add =",
        r"\bfraction = \{": ("common/ai_budget", "weight = {"),
        r"\bstatic_m([ai][xn])(\s*)=\s*\{": ("common/ai_budget", r"desired_m\1\2=\2{"),
        r"^(\s+)([^#]*?\bbuildings_(?:simple_allow|no_\w+) = yes)": ("common/buildings", r"\1# \2", ),  # removed
        # r"(\"NAME_[^-\s\"]+)-([^-\s\"]+)\"": r'\1_\2"', mostly but not generally done
    },
    "targets4": {
        r"\bany_system_(?:planet|colony) = \{[^{}#]*(?:has_owner = yes|is_colony = yes|exists = owner)\s": [
            r"any_system_(?:planet|colony) = (\{[^{}#]*)(?:has_owner = yes|is_colony = yes|exists = owner)\b",
            r"any_system_colony = \1has_owner = yes",
        ],
        r"\s(?:every|random|count|ordered)_system_planet = \{[^{}#]*limit = \{\s*(?:has_owner = yes|is_colony = yes|exists = owner)\s": [
            r"(every|random|count|ordered)_system_planet = (\{[^{}#]*limit = \{\s*)(?:has_owner = yes|is_colony = yes|exists = owner)\b",
            r"\1_system_colony = \2has_owner = yes",
        ],
        r"(\bOR = \{\s+(has_trait = trait_(?:plantoid|lithoid)_budding\s+){2}\})": "has_budding_trait = yes",
        r"_pop = \{\s+unemploy_pop = yes\s+kill_pop = yes": [
            r"(_pop = \{\s+)unemploy_pop = yes\s+(kill_pop = yes)",
            r"\1\2",
        ],  # ghost pop bug fixed
    },
}
""" v3.4
name  list syntax update
- new country_limits - replaced empire_limit
- new agreement_presets - replaced subjects
For performance reason option
"""
v3_4 = {
    "targetsR": [
        [r"^\s+empire_limit = \{", ("common/ship_sizes"
                            'v3.4: "empire_limit" has been replaces by "ai_ship_data" and "country_limits"'),
        ],
        [r"^\s+(?:ship_data|army_data) = \{", ("common/country_types"
                            'v3.4: "ship_data & army_data" has been replaces by "ai_ship_data" and "country_limits"'),
        ],
        r"\b(fire_warning_sign|add_unity_times_empire_size) = yes",
        r"\boverlord_has_(num_constructors|more_than_num_constructors|num_science_ships|more_than_num_science_ships)_in_orbit\b",
    ],
    "targets3": {
        r"\bis_subject_type = vassal": "is_subject = yes",
        r"\bis_subject_type = (\w+)": r"any_agreement = { agreement_preset = preset_\1 }",
        r"\bpreset = (tributary|vassal|satellite|scion|signatory|subsidiary|protectorate|dominion|thrall|satrapy)": r"preset = preset_\1",
        r"\bsubject_type = (\w+)": r"preset = preset_\1",
        r"\badd_100_unity_per_year_passed =": "add_500_unity_per_year_passed =",
        r"\bcount_drones_to_recycle =": "count_robots_to_recycle =",
        r"\bbranch_office_building = yes": (
            "common/buildings",
            r"owner_type = corporate",
        ),
        r"\bconstruction_blocks_others = yes": (
            "common/megastructures",
            "construction_blocks_and_blocked_by = multi_stage_type",
        ),
        r"\bhas_species_flag = racket_species_flag": r"exists = event_target:racket_species is_same_species = event_target:racket_species",
    },
    "targets4": {
        # >= 3.4
        r"\n(?:\t| {4})empire_limit = \{\s+base = [\w\W]+\n(?:\t| {4})\}": [
            r"(\s+)empire_limit = \{(\s+)base = (\d+\s+max = \d+|\d+)[\w\W]+?(?(1)\s+\})\s+\}",
            ("common/ship_sizes", r"\1ai_ship_data = {\2min = \3\1}"),
        ],
        r"\bpotential = \{\s+always = no\s+\}": [
            "potential",
            ("common/armies", "potential_country"),
        ],
        # r"(?:\t| {4})potential = \{\s+(?:exists = )?owner[\w\W]+\n(?:\t| {4})\}": [r"potential = \{\s+(?:exists = owner)?(\s+)owner = \{\s+([\w\W]+?)(?(1)\s+\})\s+\}", ("common/armies", r'potential_country = { \2 }')],
        r"\s+construction_block(?:s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no": [
            r"construction_block(s_others = no\s+construction_blocked_by|ed_by_others = no\s+construction_blocks|ed_by)_others = no",
            ("common/megastructures", "construction_blocks_and_blocked_by = self_type"),
        ],
        r"construction_blocks_others = no": [
            "construction_blocks_others = no",
            ("common/megastructures", "construction_blocks_and_blocked_by = none"),
        ],  # normally targets3 but needs after group check
        # r"construction_blocked_by_others = no": ("common/megastructures", 'construction_blocks_and_blocked_by = self_type'),
        r"(?:contact|any_playable)_country = \{\s+(?:NOT = \{\s+)?(?:any|count)_owned_(?:fleet|ship) = \{": [
            r"(any|count)_owned_(fleet|ship) =",
            r"\1_controlled_\2 =",
        ],  # only playable empire!?
        # r"\s+every_owned_fleet = \{\s+limit\b": [r"owned_fleet", r"controlled_fleet"], # only playable empire and not with is_ship_size!?
        # r"\s+(?:any|every|random)_owned_ship = \{": [r"(any|every|random)_owned_ship =", r"\1_controlled_fleet ="], # only playable empire!?
        r"\s+(?:%s)_(?:system|planet) = \{(?:\s+limit = \{)?\s+has_owner = yes\s+is_owned_by" % VANILLA_PREFIXES: [
            r"(%s)_(system|planet) =" % VANILLA_PREFIXES,
            r"\1_\2_within_border =",
        ],
        r"\b(NO[RT] = \{\s*(has_trait = trait_(?:zombie|nerve_stapled|robot_suppressed|syncretic_proles)\s+){2,4}\s*\})": (
            NO_TRIGGER_FOLDER,
            "can_think = yes",
        ),
        r"\b(?:has_trait = trait_(?:zombie|nerve_stapled|robot_suppressed|syncretic_proles)\s+){2,4}": [
            r"(?:has_trait = trait_(?:zombie|nerve_stapled|robot_suppressed|syncretic_proles)(\s+)){2,4}",
            (NO_TRIGGER_FOLDER, r"can_think = no\1"),
        ],
        r"(\bOR = \{\s*(species_portrait = human(?:_legacy)?\s+){2}\})": "is_human_species = yes",
        r"\bNO[RT] = \{\s*has_modifier = doomsday_\d[\w\s=]+\}": [
            r"NO[RT] = \{\s*(has_modifier = doomsday_\d\s+){5}\}",
            "is_doomsday_planet = no",
        ],
        r"\bOR = \{\s*has_modifier = doomsday_\d[\w\s=]+\}": [
            r"OR = \{\s*(has_modifier = doomsday_\d\s+){5}\}",
            "is_doomsday_planet = yes",
        ],
        r"\b(?:species_portrait = human(?:_legacy)?\s+){1,2}": [
            r"species_portrait = human(?:_legacy)?(\s+)(?:species_portrait = human(?:_legacy)?)?",
            r"is_human_species = yes\1",
        ],
        r"\bvalue = subject_loyalty_effects\s+\}\s+\}": [
            r"(subject_loyalty_effects\s+\})(\s+)\}",
            (
                "common/agreement_presets",
                r"\1\2\t{ key = protectorate value = subject_is_not_protectorate }\2}",
            ),
        ],
    },
}
""" v3.3 TODO soldier_job_check_trigger
ethics  value -> base
-empire_size_penalty_mult = 1.0
+empire_size_pops_mult = -0.15
+empire_size_colonies_mult = 0.5
-country_admin_cap_add = 15
+country_unity_produces_mult = 0.05
"""
v3_3 = {
    "targetsR": [
        r"\btech_repeatable_improved_edict_length",
        r"\bcountry_admin_cap_(add|mult)",
        [r"\bbuilding(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow) =", ("common/buildings", "")],  # replaced buildings ai
        [r"\bmodification = (?:no|yes)\s*", ("common/traits",
                'v3.3: "modification" flag which has been deprecated. Use "species_potential_add", "species_possible_add" and "species_possible_remove" triggers instead.'),
        ],
    ],
    "targets3": {
        r"\s+building(_basic_income_check|_relaxed_basic_income_check|s_upgrade_allow) = (?:yes|no)\n?": (
            "common/buildings",
            "",
        ),
        # r"\bGFX_ship_part_auto_repair": (["common/component_sets", "common/component_templates"], 'GFX_ship_part_ship_part_nanite_repair_system'), # because icons.gfx
        r"\b(country_election_)influence_(cost_mult)": r"\1\2",
        r"\bwould_work_job": ("common/game_rules", "can_work_specific_job"),
        r"\bhas_civic = civic_reanimated_armies": "is_reanimator = yes",
        # r"^(?:\t\t| {4,8})value =": ("common/ethics", 'base ='), maybe too cheap
        # r"\bcountry_admin_cap_mult\b": ("common/**", 'empire_size_colonies_mult'),
        # r"\bcountry_admin_cap_add\b": ("common/**", 'country_edict_fund_add'),
        # r"\bcountry_edict_cap_add\b": ("common/**", 'country_power_projection_influence_produces_add'),
        r"\bjob_administrator": "job_politician",
        r"\b(has_any_(?:farming|generator)_district)\b": r"\1_or_building",  # 3.3.4 scripted trigger
        r"^\t\tvalue\b": ("common/ethics", "base"),
        # Replaces only in filename with species
        r"^(\s+)modification = (?:no|yes)\s*?\n": {
            "species": (
                "common/traits",
                r"\1species_potential_add = { always = no }\n",
                "",
            )
        },  # "modification" flag which has been deprecated. Use "species_potential_add", "species_possible_add" and "species_possible_remove" triggers instead.
    },
    "targets4": {
        r"(?:random_weight|pop_attraction(_tag)?|country_attraction)\s+value =": [
            r"\bvalue\b",
            ("common/ethics", "base"),
        ],
        # r"\n\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}": [r"([\t ]+)NO[TR] = \{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR] = \{\s*([^{}#\r\n]+)\s*\}", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"], not valid if in OR
        r"\bany_\w+ = \{[^{}]+?\bcount\s*[<=>]+\s*[^{}\s]+?\s+[^{}]*\}": [
            r"\bany_(\w+) = \{\s*(?:([^{}]+?)\s+(\bcount\s*[<=>]+\s*[^{}\s]+)|(\bcount\s*[<=>]+\s*[^{}\s]+)\s+([^{}]*))\s+\}",
            r"count_\1 = { limit = { \2\5 } \3\4 }",
        ],  # too rare!? only simple supported TODO
    },
}
v3_2 = {
    "targetsR": [
        [r"\bslot = 0", "v3.2: set_starbase_module = now starts with 1"],
        [r"\bany_pop\b", "use any_owned_pop/any_species_pop"],
        [r"[^# \t]\s+is_planet_class = pc_ringworld_habitable\b",
            'v3.2: could possibly be replaced with "is_ringworld = yes"'
        ],
        # r"\badd_tech_progress_effect = ", # replaced with add_tech_progress
        # r"\bgive_scaled_tech_bonus_effect = ", # replaced with add_monthly_resource_mult
        [r"\bdistricts_build_district\b", ("common/districts", "REMOVED in v3.2")],  # scripted trigger
        [r"\b(drone|worker|specialist|ruler)_job_check_trigger\b", ("common/pop_jobs", "REMOVED in v3.2")],
        [r"\bspecies_planet_slave_percentage\b", "REMOVED in v3.2"],
    ],
    "targets3": {
        # r"\bis_planet_class = pc_ringworld_habitable\b": "is_ringworld = yes",
        r"\bfree_guarantee_days = \d+": "",
        r"\badd_tech_progress_effect": "add_tech_progress",
        r"\bgive_scaled_tech_bonus_effect": "add_monthly_resource_mult",
        r"\bclear_uncharted_space = \{\s*from = ([^\n{}# ])\s*\}": r"clear_uncharted_space = \1",
        r"\bhomeworld =": ("common/governments/civics", "starting_colony ="),
        # r"^((?:\t|    )parent = planet_jobs)\b": ("common/economic_categories", r"\1_productive"), TODO
        r"^(\t| )energy = (\d+|@\w+)": (
            "common/terraform",
            r"\1resources = {\n\1\1category = terraforming\n\1\1cost = { energy = \2 }\n\1}",
        ),
    },
    "targets4": {
        r"\bNO[RT] = \{\s*is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex))?\s*\}": [
            r"\bNO[RT] = \{\s*is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_cybrex))?\s*\}",
            r"is_artificial = no",
        ],
        r"\n\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex))?\b": [
            r"\bis_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)\s+is_planet_class = (?:pc_ringworld_habitable|pc_habitat|pc_cybrex)(?:\s+is_planet_class = (?:pc_ringworld_habitable|pc_cybrex))?\b",
            r"is_artificial = yes",
        ],
        r"\n\s+possible = \{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)(?:drone|worker|specialist|ruler)_job_check_trigger = yes\s*": [
            r"(\s+)(possible = \{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?))(drone|worker|specialist|ruler)_job_check_trigger = yes\s*",
            ("common/pop_jobs", r"\1possible_precalc = can_fill_\4_job\1\2"),
        ],  # only with 6 possible prior lines
        r"(?:[^b]\n\n|[^b][^b]\n)\s+possible = \{(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?(?:\n.*\s*?|\s*)|\s*)|\s*)|\s*)|\s*)|\s*)complex_specialist_job_check_trigger = yes\s*": [
            r"\n(\s+)(possible = \{(\1\t)?(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3(?(3).*\3|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)?|\s*?)complex_specialist_job_check_trigger = yes\s*)",
            ("common/pop_jobs", r"\1possible_precalc = can_fill_specialist_job\1\2"),
        ],  # only with 6 possible prior lines
    },
}
# """== 3.1 Quick stats ==
# 6 effects removed/renamed.
# 8 triggers removed/renamed.
# 426 modifiers removed/renamed.
# 1 scope removed.
# """
# prikki country removed
v3_1 = {
    "targetsR": [
        [r"\b(any|every|random)_(research|mining)_station\b", "v3.1: use just mining_station/research_station instead"],  # = 2 trigger & 4 effects
        [r"\bobservation_outpost = \{\s*limit", "v3.1: is now a scope (from planet) rather than a trigger/effect"],
        r"\bpop_can_live_on_planet\b",  # r"\1can_live_on_planet", needs planet target
        r"\bcount_armies\b",  # (scope split: depending on planet/country)
        [r"^\s+icon_frame = \d+", (["common/bombardment_stances", "common/ship_sizes"], 'v3.1: "icon_frame" now only used for starbases')], # [6-9]  # Value of 2 or more means it shows up on the galaxy map, 1-5 denote which icon it uses on starbase sprite sheets (e.g. gfx/interface/icons/starbase_ship_sizes.dds)
        # PRE TEST
        # r"\bspaceport\W", # scope replace?
        # r"\bhas_any_tradition_unlocked\W", # replace?
        # r"\bmodifier = \{\s*mult", # => factor
        # r"\bcount_diplo_ties",
        # r"\bhas_non_swapped_tradition",
        # r"\bhas_swapped_tradition",
        r"\bwhich = \"?\w+\"?\s+value\s*[<=>]\s*\{\s*scope =",  # var from 3.0
        # re.compile(r"\bwhich = \"?\w+\"?\s+value\s*[<=>]\s*(prev|from|root|event_target:[^\.\s]+)+\s*\}", re.I), # var from 3.0
    ],
    "targets3": {
        r"(\s+set_)(primitive) = yes": r"\1country_type = \2",
        # r"(\s+)count_armies": r"\1count_owned_army", # count_planet_army (scope split: depending on planet/country)
        # r"(\s+)(icon_frame = [0-5])": "", # remove
        r"text_icon = military_size_space_creature": (
            "common/ship_sizes",
            "icon = ship_size_space_monster",
        ),
        # conflict used for starbase
        # r"icon_frame = 2": ("common/ship_sizes", lambda p: p.group(1)+"icon = }[p.group(2)]),
        r"text_icon = military_size_": (
            "common/ship_sizes",
            "icon = ship_size_military_",
        ),
        # r"\s+icon_frame = \d": (["common/bombardment_stances", "common/ship_sizes"], ""), used for starbase
        r"^\s+robotic = (yes|no)[ \t]*\n": ("common/species_classes", ""),
        r"^(\s+icon)_frame = ([1-9][0-4]?)": (
            "common/armies",
            lambda p: (
                p.group(0)
                if not p.group(2) or int(p.group(2)) > 14
                else p.group(1)
                + " = GFX_army_type_"
                + {
                    "1": "defensive",
                    "2": "assault",
                    "3": "rebel",
                    "4": "robot",
                    "5": "primitive",
                    "6": "gene_warrior",
                    "7": "clone",
                    "8": "xenomorph",
                    "9": "psionic",
                    "10": "slave",
                    "11": "machine_assault",
                    "12": "machine_defensive",
                    "13": "undead",
                    "14": "imperial",
                }[p.group(2)]
            ),
        ),
        r"^(\s+icon)_frame = (\d+)": (
            "common/planet_classes",
            lambda p: (
                p.group(0)
                if not p.group(2) or int(p.group(2)) > 32
                else p.group(1)
                + " = GFX_planet_type_"
                + {
                    "1": "desert",
                    "2": "arid",
                    "3": "tundra",
                    "4": "continental",
                    "5": "tropical",
                    "6": "ocean",
                    "7": "arctic",
                    "8": "gaia",
                    "9": "barren_cold",
                    "10": "barren",
                    "11": "toxic",
                    "12": "molten",
                    "13": "frozen",
                    "14": "gas_giant",
                    "15": "machine",
                    "16": "hive",
                    "17": "nuked",
                    "18": "asteroid",
                    "19": "alpine",
                    "20": "savannah",
                    "21": "ringworld",
                    "22": "habitat",
                    "23": "shrouded",
                    "25": "city",
                    "26": "m_star",
                    "27": "f_g_star",
                    "28": "k_star",
                    "29": "a_b_star",
                    "30": "pulsar",
                    "31": "neutron_star",
                    "32": "black_hole",
                }[p.group(2)]
            ),
        ),
        r"^(\s+icon) = (\d+)": (
            "common/colony_types",
            lambda p: (
                p.group(0)
                if not p.group(2) or int(p.group(2)) > 31
                else p.group(1)
                + " = GFX_colony_type_"
                + {
                    "1": "urban",
                    "2": "mine",
                    "3": "farm",
                    "4": "generator",
                    "5": "foundry",
                    "6": "factory",
                    "7": "refinery",
                    "8": "research",
                    "9": "fortress",
                    "10": "capital",
                    "11": "normal_colony",
                    "12": "habitat",
                    "13": "rural",
                    "14": "resort",
                    "15": "penal",
                    "16": "primitive",
                    "17": "dying",
                    "18": "workers",
                    "19": "habitat_energy",
                    "20": "habitat_leisure",
                    "21": "habitat_trade",
                    "22": "habitat_research",
                    "23": "habitat_mining",
                    "24": "habitat_fortress",
                    "25": "habitat_foundry",
                    "26": "habitat_factory",
                    "27": "habitat_refinery",
                    "28": "bureaucratic",
                    "29": "picker",
                    "30": "fringe",
                    "31": "industrial",
                }[p.group(2)]
            ),
        ),
        # r"(\s+modifier) = \{\s*mult": r"\1 = { factor", now multiline
        # r"(\s+)pop_can_live_on_planet": r"\1can_live_on_planet", needs planet target
        r"\bcount_diplo_ties": "count_relation",
        r"\bhas_non_swapped_tradition": "has_active_tradition",
        r"\bhas_swapped_tradition": "has_active_tradition",
        r"\bis_for_colonizeable": "is_for_colonizable",
        r"\bcolonizeable_planet": "colonizable_planet",
        r"\bis_country\b": "is_same_empire",
    },
    "targets4": {
        # but not used for starbases
        r"\bis_space_station = no\s*icon_frame = \d+": [
            r"(is_space_station = no\s*)icon_frame = ([1-9][0-2]?)",
            (
                "common/ship_sizes",
                lambda p: p.group(1)
                + "icon = ship_size_"
                + {
                    "1": "military_1",
                    "2": "military_1",
                    "3": "military_2",
                    "4": "military_4",
                    "5": "military_8",
                    "6": "military_16",
                    "7": "military_32",
                    "8": "science",
                    "9": "constructor",
                    "10": "colonizer",
                    "11": "transport",
                    "12": "space_monster",
                }[p.group(2)],
            ),
        ],
        r"\{\s*which = \"?\w+\"?\s+value\s*[<=>]+\s*(?:prev|from|root|event_target:[^\.\s])+\s*\}": [
            r"(\s*which = \"?(\w+)\"?\s+value\s*[<=>]+\s*(prev|from|root|event_target:[^\.\s])+)",
            r"\1.\2",
        ],
        r"\bset_variable = \{\s*which = \"?\w+\"?\s+value = (?:event_target:[^\d:{}#\s=\.]+|(prev\.?|from\.?|root|this|megastructure|planet|country|owner|controller|space_owner|ship|pop|fleet|galactic_object|leader|army|ambient_object|species|pop_faction|war|federation|starbase|deposit|sector|archaeological_site|first_contact|spy_network|espionage_operation|espionage_asset)+)\s*\}": [
            r"set_variable = \{\s*which = \"?(\w+)\"?\s+value = (event_target:\w+|\w+)\s*\}",
            r"set_variable = { which = \1 value = \2.\1 }",
        ],
        r"\s+spawn_megastructure = \{[^{}#]+?location = [\w\.:]+": [
            r"(spawn_megastructure = \{[^{}#]+?)location = ([\w\.:]+)",
            r"\1coords_from = \2",
        ],
        r"\s+modifier = \{\s*mult\b": [r"\bmult\b", "factor"],
    },
}
if code_cosmetic and not only_warning:
    v3_1["targets4"][
        r"(?:has_(?:valid_)?civic = civic_(?:corporate_)?crafters\s+?){2}"
    ] = (NO_TRIGGER_FOLDER, "is_crafter_empire = yes")
    v3_1["targets4"][
        r"(?:has_(?:valid_)?civic = civic_(?:pleasure_seekers|corporate_hedonism)\s+?){2}"
    ] = (NO_TRIGGER_FOLDER, "is_pleasure_seeker = yes")
    v3_1["targets4"][
        r"(?:has_(?:valid_)?civic = civic_(?:corporate_|hive_|machine_)?catalytic_processing\s+?){3,4}"
    ] = (NO_TRIGGER_FOLDER, "is_catalytic_empire = yes")

# 3.0 removed ai_weight for buildings except branch_office_building = yes
v3_0 = {
    "targetsR": [
        r"\bproduced_energy\b",
        r"\b(ship|army|colony|station)_maintenance\b",
        r"\b(construction|trade|federation)_expenses\b",
        r"\bhas_(population|migration)_control = (yes|no)",
        r"\b(%s)_planet\b" % VANILLA_PREFIXES,  # split in owner and galaxy and system scope
        r"\b(%s)_ship\b" % VANILLA_PREFIXES,  # split in owner and galaxy and system scope
        [r"^\s+ai_weight =", ("common/buildings",
                        "v3.0: ai_weight for buildings removed except for branch office"), # replaced buildings ai
        ],
    ],
    "targets3": {
        r"\b(first_contact_)attack_not_allowed": r"\1cautious",
        r"\bsurveyed = \{": "set_surveyed = {",
        r"(\s+)set_surveyed = (yes|no)": r"\1surveyed = \2",
        r"has_completed_special_project\s+": "has_completed_special_project_in_log ",
        r"has_failed_special_project\s+": "has_failed_special_project_in_log ",
        r"species = last_created(\s)": r"species = last_created_species\1",
        r"owner = last_created(\s)": r"owner = last_created_country\1",
        r"(\s(?:%s))_pop =" % VANILLA_PREFIXES: r"\1_owned_pop =",
        r"(\s(?:%s))_planet =" % VANILLA_PREFIXES: r"\1_galaxy_planet =",  # _system_planet
        r"(\s(?:%s))_ship =" % VANILLA_PREFIXES: r"\1_fleet_in_system =",  # _galaxy_fleet
        r"(\s(?:%s))_sector =" % VANILLA_PREFIXES: r"\1_owned_sector =",  # _galaxy_sector
        r"(\s(?:any|every|random))_war_(attacker|defender) =": r"\1_\2 =",
        r"(\s(?:%s))_recruited_leader =" % VANILLA_PREFIXES: r"\1_owned_leader =",
        r"\bcount_planets\s+": "count_system_planet  ",  # count_galaxy_planet
        r"\bcount_ships\s+": "count_fleet_in_system ",  # count_galaxy_fleet
        r"\bcount(_owned)?_pops\s+": "count_owned_pop ",
        r"\bcount_(owned|fleet)_ships\s+": "count_owned_ship ",  # 2.7
        # "any_ship_in_system": "any_fleet_in_system", # works only sure for single size fleets
        r"\bspawn_megastructure = \{([^{}#]+)location =": r"spawn_megastructure = {\1planet =",  # s.a. multiline coords_from
        r"\s+planet = (solar_system|planet)[\s\n\r]*": "",  # REMOVE
        r"(\s+)any_system_within_border = \{\s*any_system_planet = (.*?\s*\})\s*\}": r"\1any_planet_within_border = \2",  # very rare, maybe put to cosmetic
        r"is_country_type = default\s+has_monthly_income = \{\s*resource = (\w+) value <=? \d": r"no_resource_for_component = { RESOURCE = \1",
        r"([^\._])owner = \{\s*is_same_(?:empire|value) = ([\w\.:]+)\s*\}": r"\1is_owned_by = \2",
        r"(\s+)is_(?:country|same_value) = ([\w\.:]+\.(?:controller|(?:space_)?owner)(?:\.overlord)?(?:[\s}]+|$))": r"\1is_same_empire = \2",
        r"((?:controller|(?:space_)?owner|overlord|country) = \{|is_ai = (?:yes|no))\s+is_same_value\b": r"\1 is_same_empire",
        ## Since Megacorp removed: change_species_characteristics was false documented until 3.2
        r"[\s#]+(pops_can_(be_colonizers|migrate|reproduce|join_factions|be_slaves)|can_generate_leaders|pops_have_happiness|pops_auto_growth|pop_maintenance) = (yes|no)\s*": "",
    },
    "targets4": {
        r"\s+random_system_planet = \{\s*limit = \{\s*is_primary_star = yes\s*\}": [
            r"(\s+)random_system_planet = \{\s*limit = \{\s*is_primary_star = yes\s*\}",
            r"\1star = {",
        ],  # TODO works only on single star systems
        r"\s+random_system_planet = \{\s*limit = \{\s*is_star = yes\s*\}": [
            r"(\s+)random_system_planet = \{\s*limit = \{\s*is_star = yes\s*\}",
            r"\1star = {",
        ],  # TODO works only on single star systems
        r"\bcreate_leader = \{[^{}]+?\s+type = \w+": [
            r"(create_leader = \{[^{}]+?\s+)type = (\w+)",
            r"\1class = \2",
        ],
        r"\s(?:every|random|count)_(?:playable_)?country = \{[^{}#]*limit = \{\s*(?:NO[TR] = \{)?\s*is_same_value\b": [
            "is_same_value",
            "is_same_empire",
        ],
        r"\bOR = \{\s*(has_crisis_level = crisis_level_5\s+|has_country_flag = declared_crisis){2}\}": (
            ["common/scripted_effects", "events"],
            "has_been_declared_crisis = yes",
        ),
    },
}
if code_cosmetic and not only_warning:
    v3_0["targets3"][r"\bhas_crisis_level = crisis_level_5\b"] = (
        NO_TRIGGER_FOLDER,
        "has_been_declared_crisis = yes",
    )

actuallyTargets = {
    "targetsR": [
        r"\bcan_support_spaceport = (yes|no)",  # < 2.0
        [r"\bnum_\w+\s*[<=>]+\s*[a-z]+[\s}]", "no scope alone", ],  #  [^\d{$@] too rare (could also be auto fixed)
        [r"^\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}", "can be merged to NOR if not in an OR", ],  #  [^\d{$@] too rare (could also be auto fixed)
    ],
    # targets2 = {
    #   r"MACHINE_species_trait_points_add = \d" : ["MACHINE_species_trait_points_add ="," ROBOT_species_trait_points_add = ",""],
    #   r"job_replicator_add = \d":["if = {limit = {has_authority = \"?auth_machine_intelligence\"?} job_replicator_add = ", "} if = {limit = {has_country_flag = synthetic_empire} job_roboticist_add = ","}"]
    # }
    "targets3": {
        r"\bstatic_rotation = yes\s*": ("common/component_templates", ""),
        r"\bowner\.species\b": "owner_species",
        ### < 2.2
        r"\bhas_job = unemployed\b": "is_unemployed = yes",
        ### somewhat older
        r"(\s+)ship_upkeep_mult =": r"\1ships_upkeep_mult =",
        r"\b(contact_rule = )script_only": (
            "common/country_types",
            r"\1on_action_only",
        ),
        r"\b(any|every|random)_(research|mining)_station\b": r"\2_station", # ??
        r"(\s+)add_(%s) = (-?@\w+|-?\d+)" % RESOURCE_ITEMS: r"\1add_resource = { \2 = \3 }",
        r"\bhas_ethic = (\"?)ethic_gestalt_consciousness\1\b":  (NO_TRIGGER_FOLDER, "is_gestalt = yes"),
        r"\bhas_authority = (\"?)auth_machine_intelligence\1\b":  (NO_TRIGGER_FOLDER, "is_machine_empire = yes"),
        r"\bhas_authority = (\"?)auth_hive_mind\1\b":  (NO_TRIGGER_FOLDER, "is_hive_empire = yes"),
        r"\bhas_authority = (\"?)auth_corporate\1\b":  (NO_TRIGGER_FOLDER, "is_megacorp = yes"),
    },
    "targets4": {
        ### < 3.0
        r"\s+every_planet_army = \{\s*remove_army = yes\s*\}": [
            r"every_planet_army = \{\s*remove_army = yes\s*\}",
            r"remove_all_armies = yes",
        ],
        r"\s(?:%s)_neighbor_system = \{[^{}]+?\s+ignore_hyperlanes = (?:yes|no)\n?" % VANILLA_PREFIXES: [
            r"(_neighbor_system)( = \{[^{}]+?)\s+ignore_hyperlanes = (yes|no)\n?",
            lambda p: (
                p.group(1) + p.group(2)
                if p.group(3) == "no"
                else p.group(1) + "_euclidean" + p.group(2)
            ),
        ],
        r"\bNO[RT] = \{\s*has_ethic = \"?ethic_(?:(?:%s)|fanatic_(?:%s))\"?\s+has_ethic = \"?ethic_(?:(?:%s)|fanatic_(?:%s))\"?\s+\}"
        % (VANILLA_ETHICS, VANILLA_ETHICS, VANILLA_ETHICS, VANILLA_ETHICS): [
            r"NO[RT] = \{\s*has_ethic = \"?ethic_(?:(%s)|fanatic_(%s))\"?\s+has_ethic = \"?ethic_(?:(?:\1|\2)|fanatic_(?:\1|\2))\"?\s+\}"
            % (VANILLA_ETHICS, VANILLA_ETHICS),
            (NO_TRIGGER_FOLDER, r"is_\1\2 = no"),
        ],
        r"\b(?:OR = \{)?\s+?has_ethic = \"?ethic_(?:(?:%s)|fanatic_(?:%s))\"?\s+has_ethic = \"?ethic_(?:(?:%s)|fanatic_(?:%s))\"?\s*\}?"
        % (VANILLA_ETHICS, VANILLA_ETHICS, VANILLA_ETHICS, VANILLA_ETHICS): [
            r"(\bOR = \{)?(\s*?\n*?\s*?)?(?(1)\t?)has_ethic = \"?ethic_(?:(%s)|fanatic_(%s))\"?\s*?has_ethic = \"?ethic_(?:(?:\4|\3)|fanatic_(?:\4|\3))\"?\s*?(?(1)\})"
            % (VANILLA_ETHICS, VANILLA_ETHICS),
            (NO_TRIGGER_FOLDER, r"\2is_\3\4 = yes"),
        ],  # r"\4is_ethics_aligned = { ARG1 = \2\3 }",
        ### Boolean operator merge
        # NAND <=> OR = { NOT
        r"\s+OR = \{(?:\s*NOT = \{[^{}#]*?\})+\s*\}[ \t]*\n": [
            r"^(\s+)OR = \{\s*?\n(?:(\s+)NOT = \{\s+)?([^{}#]*?)\s*\}(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?(?:(\s+)?NOT = \{\s*([^{}#]*?)\s*\})?",
            r"\1NAND = {\n\2\3\4\5\6\7\8\9\10\11\12\13\14\15",
        ],  # up to 7 items (sub-trigger)
        # NOR <=> AND = { NOT
        r"\n\s+AND = \{\s(?:\s+NOT = \{\s*(?:[^{}#]+|\w+ = {[^{}#]+\})\s*\}){2,}\s+\}?": [
            r"(\n\s+)AND = \{\s*?(?:(\n\s+)NOT = \{\s*([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s+\})(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\4(?(4)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\7(?(7)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\10(?(10)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\13(?(13)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\16(?(16)(?=((\2)?NOT = \{\s+([^{}#]+?|\w+ = \{[^{}#]+\s*\})\s*\})?)\19)?)?)?)?)?\1\}",
            r"\1NOR = {\2\3\5\6\8\9\11\12\14\15\17\18\20\21\1}",
        ],  # up to 7 items (sub-trigger)
        # NOR <=> (AND) = { NOT
        r"(?<![ \t]OR) = \{\s(?:[^{}#\n]+\n)*(?:\s+NO[RT] = \{\s*[^{}#]+?\s*\}){2,}": [
            r"(\n\s+)NO[RT] = \{\1(\s+)([^{}#]+?)\s+\}\s+NO[RT] = \{\s*([^{}#]+?)\s+\}", (re.compile(r"^(?!common/governments)"),
            r"\1NOR = {\1\2\3\1\2\4\1}"),
        ],  # only 2 items (sub-trigger) (?<!\sOR) Negative Look-behind
        # NAND <=> NOT = { AND
        r"\n\s+NO[RT] = \{\s*AND = \{[^{}#]*?\}\s*\}": [
            r"(\t*)NO[RT] = \{\s*AND = \{[ \t]*\n(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?(?:\t([^{}#\n]+\n))?\s*\}[ \t]*\n",
            r"\1NAND = {\n\2\3\4\5",
        ],  # only 4 items (sub-trigger)
        # NOR <=> NOT = { OR (only sure if base is AND)
        r"\n\s+NO[RT] = \{\s*?OR = \{\s*(?:\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+?){2,}\}\s*\}": [
            r"(\t*)NO[RT] = \{\s*?OR = \{(\s+)(\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s+)(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?(\s*\w+ = (?:[^{}#\s=]+|\{[^{}#\s=]+\s*\})\s)?\s*\}\s+",
            r"\1NOR = {\2\3\4\5\6\7",
        ],  # only right indent for 5 items (sub-trigger)
        ### End boolean operator merge
        r"\bany_country = \{[^{}#]*(?:has_event_chain|is_ai = no|is_country_type = default|has_policy_flag|(?:is_zofe_compatible|merg_is_default_empire|is_galactic_community_member|is_part_of_galactic_council) = yes)": [
            r"any_country = (\{[^{}#]*(?:has_event_chain|is_ai = no|is_country_type = default|has_policy_flag|(?:is_zofe_compatible|merg_is_default_empire|is_galactic_community_member|is_part_of_galactic_council) = yes))",
            r"any_playable_country = \1",
        ],
        r"\s(?:every|random|count)_country = \{[^{}#]*limit = \{\s*(?:has_event_chain|is_ai = no|is_country_type = default|has_policy_flag|(?:is_zofe_compatible|merg_is_default_empire|is_galactic_community_member|is_part_of_galactic_council) = yes)": [
            r"(\s(?:every|random|count))_country = (\{[^{}#]*limit = \{\s*(?:has_event_chain|is_ai = no|is_country_type = default|has_policy_flag|(?:is_zofe_compatible|merg_is_default_empire|is_galactic_community_member|is_part_of_galactic_council) = yes))",
            r"\1_playable_country = \2",
        ],
        r"\{\s+owner = \{\s*is_same_(?:empire|value) = [\w\.:]+\s*\}\s*\}": [
            r"\{\s+owner = \{\s*is_same_(?:empire|value) = ([\w\.:]+)\s*\}\s*\}",
            r"{ is_owned_by = \1 }",
        ],
        r"NO[RT] = \{\s*(?:is_country_type = (?:awakened_)?fallen_empire\s+){2}\}": "is_fallen_empire = no",
        r"\n\s+(?:OR = \{)?\s{4,}(?:is_country_type = (?:awakened_)?fallen_empire\s+){2}\}?": [
            r"(\s+)(OR = \{)?(?(2)\s{4,}|(\s{4,}))is_country_type = (?:awakened_)?fallen_empire\s+is_country_type = (?:awakened_)?fallen_empire(?(2)\1\})",
            (NO_TRIGGER_FOLDER, r"\1\3is_fallen_empire = yes"),
        ],
        r"\bNO[RT] = \{\s*is_country_type = (?:default|awakened_fallen_empire)\s+is_country_type = (?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = no",
        r"\bOR = \{\s*is_country_type = (?:default|awakened_fallen_empire)\s+is_country_type = (?:default|awakened_fallen_empire)\s+\}": "is_country_type_with_subjects = yes",
        r"\s+(?:OR = \{)?\s+(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+\}?": [
            r"(\s+)(OR = \{)?(?(2)\s+|(\s+))(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)(?(2)\1\})",
            (NO_TRIGGER_FOLDER, r"\1\3is_synthetic_empire = yes"),
        ],  # \s{4,}
        r"NO[RT] = \{\s*(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+(?:has_authority = \"?auth_machine_intelligence\"?|has_country_flag = synthetic_empire|is_machine_empire = yes)\s+\}": "is_synthetic_empire = no",
        r"NO[RT] = \{\s*has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s*has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s*has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s*\}": (NO_TRIGGER_FOLDER, "is_homicidal = no"),
        r"(?:\bOR = \{)\s{4,}?has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s*\}?": [
            r"(\bOR = \{\s+)?has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?\s+has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm)\"?(?(1)\s*\})",
            (NO_TRIGGER_FOLDER, "is_homicidal = yes"),
        ],
        r"\b(?:has_(?:valid_)?civic = \"?civic_(?:fanatic_purifiers|machine_terminator|hive_devouring_swarm|barbaric_despoilers)\s+\"?){4}": (NO_TRIGGER_FOLDER, "is_unfriendly = yes\n"),
        r"NOT = \{\s*check_variable = \{\s*which = \"?\w+\"?\s+value = [^{}#\s=]\s*\}\s*\}": [
            r"NOT = \{\s*(check_variable = \{\s*which = \"?\w+\"?\s+value) = ([^{}#\s=])\s*\}\s*\}",
            r"\1 != \2 }",
        ],
        # r"change_species_characteristics = \{\s*?[^{}\n]*?
        r"[\s#]+new_pop_resource_requirement = \{[^{}]+\}[ \t]*": "",
        # very rare, maybe put to cosmetic
        r"\s+any_system_within_border = \{\s*any_system_planet = \{\s*(?:\w+ = \{[\w\W]+?\}|[\w\W]+?)\s*\}\s*\}": [
            r"(\n?\s+)any_system_within_border = \{(\1\s*)any_system_planet = \{\1\s*([\w\W]+?)\s*\}\s*\1\}",
            r"\1any_planet_within_border = {\2\3\1}",
        ],
        r"\s+any_system = \{\s*any_system_planet = \{\s*(?:\w+ = \{[\w\W]+?\}|[\w\W]+?)\s*\}\s*\}": [
            r"(\n?\s+)any_system = \{(\1\s*)any_system_planet = \{\1\s*([\w\W]+?)\s*\}\s*\1\}",
            r"\1any_galaxy_planet = {\2\3\1}",
        ],
        # Near cosmetic
        r"\bcount_starbase_modules = \{\s+type = \w+\s+count\s*>\s*0\s+\}": [
            r"count_starbase_modules = \{\s+type = (\w+)\s+count\s*>\s*0\s+\}",
            r"has_starbase_module = \1",
        ],
        r'\b(?:add_modifier = \{\s*modifier|set_timed_\w+ = \{\s*flag) = "?[\w@.]+"?\s+days = \d{2,}\s*?(?:\#[^\n{}]+\n\s+)?\}': [
            r"days = (\d{2,})\b",
            lambda p: (
                "years = " + str(int(p.group(1)) // 360)
                if int(p.group(1)) > 320 and int(p.group(1)) % 360 < 41
                else (
                    "months = " + str(int(p.group(1)) // 30)
                    if int(p.group(1)) > 28 and int(p.group(1)) % 30 < 3
                    else "days = " + p.group(1)
                )
            ),
        ],
        r"\brandom_list = \{\s+\d+ = \{\s*(?:(?:[\w:]+ = \{\s+\w+ = \{\n?[^{}#\n]+\}\s*\}|\w+ = \{\n?[^{}#\n]+\}|[^{}#\n]+)\s*\}\s+\d+ = \{\s*\}|\s*\}\s+\d+ = \{\s*(?:[\w:]+ = \{\s+\w+ = \{\n?[^{}#\n]+\}\s*\}|\w+ = \{\n?[^{}#\n]+\}|[^{}#\n]+)\s*\}\s*)\s*\}": [
            r"\brandom_list = \{\s+(?:(\d+) = \{\s+(\w+ = \{[^{}#\n]+\}|[^{}#\n]+)\s+\}\s+(\d+) = \{\s*\}|(\d+) = \{\s*\}\s+(\d+) = \{\s+(\w+ = \{[^{}#\n]+\}|[^{}#\n]+)\s+\})\s*",  # r"random = { chance = \1\5 \2\6 "
            lambda p: "random = { chance = "
            + str(
                round(
                    (
                        int(p.group(1)) / (int(p.group(1)) + int(p.group(3)))
                        if p.group(1) and len(p.group(1)) > 0
                        else int(p.group(5)) / (int(p.group(5)) + int(p.group(4)))
                    )
                    * 100
                )
            )
            + " "
            + (p.group(2) or p.group(6))
            + " ",
        ],
    },
}

ACTUAL_STELLARIS_VERSION_FLOAT = float(ACTUAL_STELLARIS_VERSION_FLOAT)
print("ACTUAL_STELLARIS_VERSION_FLOAT", ACTUAL_STELLARIS_VERSION_FLOAT)

# 1. Define a list of version configurations, sorted from newest to oldest.
# Each item is a tuple: (version_threshold_float, data_dictionary_for_that_version)
version_data_sources = [
    (4.0, v4_0),
    # (3.99, v3_14),
    (3.98, v3_13),
    (3.97, v3_12),
    (3.96, v3_11),
    (3.95, v3_10),
    (3.9,  v3_9),
    (3.8,  v3_8),
    (3.7,  v3_7),
    (3.6,  v3_6),
    (3.5,  v3_5),
    (3.4,  v3_4),
    (3.3,  v3_3),
    (3.2,  v3_2),
    (3.1,  v3_1),
    (3.0,  v3_0),
]

# 2. Helper function to apply data to actuallyTargets
def _apply_version_data_to_targets(source_data_dict):
    """Updates actuallyTargets with data from source_data_dict."""
    # Ensure the keys exist in source_data_dict to avoid KeyErrors
    # if a specific version dict might be structured differently (optional, for robustness).
    # Based on your script, they all have these keys.
    if "targetsR" in source_data_dict:
        actuallyTargets["targetsR"].extend(source_data_dict["targetsR"])
    if "targets3" in source_data_dict:
        actuallyTargets["targets3"].update(source_data_dict["targets3"])
    if "targets4" in source_data_dict:
        actuallyTargets["targets4"].update(source_data_dict["targets4"])

targets_trait = {
    re.compile(r"\badd_trait = \"?(\w+)\"?\b"): r"add_trait = { trait = \1 }",
    re.compile(r"\badd_trait_no_notify = \"?(\w+)\"?\b"): r"add_trait = { trait = \1 show_message = no }",
}

# Since v4.0 ,
def transform_add_trait(basename, lines, changed, targets_trait=targets_trait):
    """
    Transforms lines of a Stellaris script, replacing all occurrences of:
        add_trait = trait_name
    with:
        add_trait = { trait = trait_name }
    — unless the line appears inside a 'modify_species = {' or
    'change_species_characteristics = {' block.
    """
    # Patterns for detecting the start of excluded blocks and the trait assignment
    # block_start_pattern = re.compile(r'\b(modify_species|change_species_characteristics) = \{')

    skip_block = False
    block_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "" or stripped.startswith('#'):
            continue

        # Detect block start
        # if block_start_pattern.match(stripped):
        if (stripped.startswith('modify_species = {') or stripped.startswith('change_species_characteristics = {')):
            if not stripped.endswith('}'):
                skip_block = True
                block_depth = 1
            continue
        # Handle lines inside skipped blocks
        if skip_block:
            block_depth += stripped.count('{')
            block_depth -= stripped.count('}')
            if block_depth < 1:
                skip_block = False
            continue

        stripped_len = len(line.lstrip())
        if stripped_len < 22:
            continue

        # r"(?<!modify_species)(?<!change_species_characteristics)( = \{[^{}#]*?\badd_trait = )\"?(\w+)\"?\b([^{}#}]*?)": r"\1{ trait = \2\3 }", # cheap no look behind

        # Apply transformation if not inside skipped block
        # Only single liner supported
        if "add_trait" in stripped and not 'add_trait = {' in stripped:
            if stripped.startswith('add_trait'): # and not stripped.endswith('}')

                if stripped.startswith('add_trait ='):
                    line = f'{line[:-stripped_len]}add_trait = {{ trait = {stripped[12:]} }}\n'
                    lines[i] = line
                else:
                    line = f'{line[:-stripped_len]}add_trait = {{ trait = {stripped[22:]} show_message = no }}\n'
                    lines[i] = line
                changed = True
                logger.info(
                   "\t# Updated effect on file: %s on %s (at line %i) with %s\n"
                   % (
                       basename,
                       stripped,
                       i,
                       line.lstrip(),
                   )
                )
            else:
                for tar, repl in targets_trait.items():
                    line = tar.sub(repl, line, count=1)
                    if lines[i] != line:
                        lines[i] = line
                        changed = True
                        logger.info(
                           "\t# Updated effect on file: %s on %s (at line %i) with %s\n"
                           % (
                               basename,
                               stripped,
                               i,
                               line.lstrip(),
                           )
                        )
                        break

    return lines, changed

def do_code_cosmetic():
    global targets3, targets4
    DLC_triggers = {
        # "Anniversary Portraits",
        # "Arachnoid Portrait Pack",
        # "Creatures of the Void Portrait Pack",
        "Apocalypse": "apocalypse_dlc", # later?
        "Ancient Relics Story Pack": "ancrel",
        "Aquatics Species Pack": "aquatics",
        "Distant Stars Story Pack": "distar",
        "Federations": "federations_dlc",
        "Humanoids Species Pack": "humanoids",
        "Leviathans Story Pack": "leviathans",
        "Lithoids Species Pack": "lithoids",
        "Necroids Species Pack": "necroids",
        "Nemesis": "nemesis",
        "Overlord": "overlord_dlc",
        "Plantoids Species Pack": "plantoids",
        "Plantoid": "plantoids",
        # "Synthetic Dawn Story Pack": "synthetic_dawn", # enable it later - changed in v3.12
        "Toxoids Species Pack": "toxoids",
        "First Contact Story Pack": "first_contact_dlc",
        "Galactic Paragons": "paragon_dlc",
        "Megacorp": "megacorp",
        "Utopia": "utopia",
        "Astral Planes": "astral_planes_dlc",
        "The Machine Age": "machine_age_dlc",
        "Cosmic Storms": "cosmic_storms_dlc",
        "Rick The Cube Species Portrait": "rick_the_cube_dlc",
        "Grand Archive": "grand_archive_dlc",
        "BioGenesis": "biogenesis_dlc",
        "Stargazer Species Portrait": "stargazer_dlc",
        # "": "mammalians_micro_dlc",
    }
    triggerScopes = r"limit|trigger|any_\w+|leader|owner|controller|PREV|FROM|ROOT|THIS|event_target:\w+"
    targets3[r"(?:[<=>{]\s|\.|\t|PREV|FROM|Prev|From)+(PREV|FROM|ROOT|THIS|Prev|From|Root|This)+\b" ] = lambda p: p.group(0).lower()
    targets3[r"\b(IF|ELSE|ELSE_IF|OWNER|Owner|CONTROLLER|Controller|LIMIT) ="] = lambda p: p.group(1).lower() + " ="
    targets3[r"\b(or|not|nor|and) ="] = lambda p: p.group(1).upper() + " ="
    targets3[r" {4}"] = r"\t"  # r" {4}": r"\t", # convert space to tabs
    targets3[r"^(\s+)limit = \{\s*\}"] = r"\1# limit = { }"
    targets3[r'\bhost_has_dlc = "([\s\w]+)"'] = (
        re.compile(r"^(?!common/traits)"),
        lambda p: (
            "has_" + DLC_triggers[p.group(1)] + " = yes"
            if p.group(1) and p.group(1) in DLC_triggers
            else p.group(0)
        ),
    )
    # targets3[r"\s*days = -1\s*"] = ' ' # still needed to execute immediately
    targets3[r"(?<!(?:e\.g|.\.\.))([#.])[\t ]{1,3}([a-z])([a-z]+ +[^;:\s#=<>]+)"] = (
        lambda p: p.group(1) + " " + p.group(2).upper() + p.group(3)
    )  # format comment
    targets3[r"#([^\-\s#])"] = r"# \1"  # r"#([^\s#])": r"# \1", # format comment
    #  targets3[r"# +([A-Z][^\n=<>{}\[\]# ]+? [\w,\.;\'\//+\- ()&]+? \w+ \w+ \w+)$"] = r"# \1." # set comment punctuation mark
    targets3[r"(?<!(?:e\.g|.\.\.))([#.][\t ][a-z])([a-z]+ +[^;:\s#=<>]+ [^\n]+?[\.!?])$" ] = lambda p: p.group(1).upper() + p.group(2)  # format comment
    # NOT NUM triggers.
    targets3[r"\bNOT = \{\s*(\w+)\s*([<=>]+)\s*(@\w+|-?[\d.]+)\s+\}"] = lambda p: p.group(1) +" "+ ({
                ">": "<=",
                "<": ">=",
                ">=": "<",
                "<=": ">",
                "=": "!=",
            }[p.group(2)]  ) +" "+ p.group(3) if p.group(2) != "=" or p.group(3)[0] == "@" or p.group(3)[0] == "-" or is_float(p.group(3)) else p.group(0)
    # targets3[r"(\w+)\s*!=\s*([^\n\s<\=>{}#]+)"] = r"NOT = { \1 = \2 }"
    targets3[r"\bNOT = \{\s*(num_\w+|\w+?(?:_passed)) = (\d+)\s*\}"] = r"\1 != \2"
    targets3[r"\bfleet = \{\s*(destroy|delete)_fleet = this\s*\}"] = (
        r"\1_fleet = fleet"  # TODO may extend
    )
    targets3[r"\s+change_all = no"] = ""  # only yes option
    targets3[r"(\s+has_(?:population|migration)_control) = (yes|no)"] = (
        r"\1 = { type = \2 country = prev.owner }"  # NOT SURE
    )
    # targets3[r"\bNOT = \{\s*has_valid_civic\b"] = "NOT = { has_civic"
    targets3[r"\bowner_main_species\b"] = "owner_species"
    targets3[
        re.compile(
            r"\bNO[RT] = \{\s*((?:%s) = \{)\s*([^\s]+) = yes\s*\}\s*\}" % triggerScopes,
            re.I,
        )
    ] = r"\1 \2 = no }"
    targets3[r"(\s|\.)(?:space_)?owner = { (?:is_country_type = default|merg_is_default_empire = (yes|no)) \}"] = lambda p: (
        (" = { can_generate_trade_value = " + p.group(2) + " }"
        if p.group(1) == "."
        else p.group(1) + "can_generate_trade_value = " + p.group(2))
        if p.group(2)
        else " = { can_generate_trade_value = yes }"
            if p.group(1) == "."
            else p.group(1) + "can_generate_trade_value = yes"
    )
    # Collect same scope
    targets4[r"exists = (\w+)\n(?:\s+\1 = \{\s*\w+ = [^{}#\n]+?\s*\}[ \t]*\n)+"] = [
            r"(\s+\w+ = \{)\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+\1\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+(?:\1\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+)?(?:\1\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+)?(?:\1\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+)?(?:\1\s*(\w+ = [^{}#\n]+)\s*\}[ \t]*\n+)?",
            r"\1 \2\3\4\5\6\7}\n"]  # up to 6 items
    targets4[r"[^#]\s+NO[RT] = \{\s*\w+? = yes\s*\}"] = [r"NO[RT] = \{\s*(\w+? = )yes\s*\}", r"\1no"]
    targets4[r"\bany_system_planet = \{\s*is_capital = (?:yes|no)\s*\}"] = [
        r"any_system_planet = \{\s*is_capital = (yes|no)\s*\}",
        r"is_capital_system = \1",
    ]
    targets4[r"(?:species|country|ship|pop|leader|army) = \{\s*is_same_value = [\w\.:]+?\.?species\s*\}"] = [
        r"(species|country|ship|pop|leader|army) = \{\s*is_same_value = ([\w\.:]+?\.?species)\s*\}",
        r"\1 = { is_same_species = \2 }"
    ]

    # targets3[r"# *([A-Z][\w ={}]+?)\.$"] = r"# \1" # remove comment punctuation mark
    # targets4[r"\n{3,}"] = "\n\n" # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    # only for planet galactic_object
    targets4[
        r"(?:(?:neighbor|rim|random|every|count|closest|ordered)_system|_planet|_system_colony|_within_border) = \{\s*?(?:limit = \{)?\s*exists = (?:space_)?owner\b"
    ] = [r"exists = (?:space_)?owner", "has_owner = yes"]  # only for planet galactic_object
    targets4[r"_event = \{\s+id = \"[\w.]+\""] = [r"\bid = \"([\w.]+)\"", ("events", r"id = \1"), ]  # trim id quote marks

    # targets4[r"\n\s+\}\n\s+else"] = [r"\}\s*else", "} else"] # r"\s*\n{2,}": "\n\n", # cosmetic remove surplus lines
    # WARNING not valid if in OR: NOR <=> AND = { NOT NOT } , # only 2 items (sub-trigger)
    targets4[r"\n\s+NO[TR] = \{\s*[^{}#\n]+\s*\}\s*?\n\s*NO[TR] = \{\s*[^{}#\n]+\s*\}"] = [
        r"([\t ]+)NO[TR] = \{\s*([^{}#\r\n]+)\s*\}\s*?\n\s*NO[TR] = \{\s*([^{}#\r\n]+)\s*\}",
        (r"^(?!governments)\w+", r"\1NOR = {\n\1\t\2\n\1\t\3\n\1}"),
    ]
    # Merge no
    targets4[r"[^#]\s+\w+ = no(?: NO[TR] = \{|\s+NO[TR] = \{\s*[^{}#\n]+\s*\})"] = [r"\b(\w+) = no\s+NO[TR] = \{", r"NOR = { \1 = yes"]
    targets4[r"[^#]\s+NO[TR] = \{[^{}#\n]+\}\s+\w+ = no"] = [r"NO[TR] = \{\s*([^{}#\n]+?)\s*\}\s+(\w+) = no$", r"NOR = { \1 \2 = yes }"]
    targets4[r"\n\s+random_country = \{\s*limit = \{\s*is_country_type = global_event\s*\}" ] = [r"random_country = \{\s*limit = \{\s*is_country_type = global_event\s*\}", "event_target:global_event_country = {", ]
    # unnecessary AND
    targets4[
        r"\b((?:%s) = \{(\s+)(?:AND|this) = \{(?:\2\t[^\n]+)+\2\}\n)" % triggerScopes] = [
        r"(%s) = \{\n(\s+)(?:AND|this) = \{\n\t(\2[^\n]+\n)(?(3)\t)(\2[^\n]+\n)?(?(4)\t)(\2[^\n]+\n)?(?(5)\t)(\2[^\n]+\n)?(?(6)\t)(\2[^\n]+\n)?(?(7)\t)(\2[^\n]+\n)?(?(8)\t)(\2[^\n]+\n)?(?(9)\t)(\2[^\n]+\n)?(?(10)\t)(\2[^\n]+\n)?(?(11)\t)(\2[^\n]+\n)?(?(12)\t)(\2[^\n]+\n)?(?(13)\t)(\2[^\n]+\n)?(?(14)\t)(\2[^\n]+\n)?(?(15)\t)(\2[^\n]+\n)?(?(16)\t)(\2[^\n]+\n)?(?(17)\t)(\2[^\n]+\n)?(?(18)\t)(\2[^\n]+\n)?(?(19)\t)(\2[^\n]+\n)?(?(20)\t)(\2[^\n]+\n)?\2\}\n"
        % triggerScopes,
        r"\1 = {\n\3\4\5\6\7\8\9\10\11\12\13\14\15\16\17\18\19\20\21",
    ]
    targets4[r"(?:\s+add_resource = \{\s*\w+ = [^\s{}#]+\s*\}){2,}"] = [
        r"(\s+add_resource = \{)(\s*\w+ = [^\s{}#]+)\s*\}\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\}(?(3)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(4)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(5)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(6)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?(?(7)\s+add_resource = \{(\s*\w+ = [^\s{}#]+)\s*\})?",
        r"\1\2\3\4\5\6\7 }",
    ]  # 6 items
    ### 3.4
    targets4[r"\s(?:\bNO[RT]|\bOR) = \{\s*has_modifier = doomsday_\d[\w\s=]+\}"] = [
        r"(N)?O[RT] = \{\s*(has_modifier = doomsday_\d\s+){5}\}",
        lambda p: "is_doomsday_planet = " + ("yes" if not p.group(1) or p.group(1) == "" else "no"),
    ]
    # targets4[r"\bOR = \{\s*has_modifier = doomsday_\d[\w\s=]+\}"] = [r"OR = \{\s*(has_modifier = doomsday_\d\s+){5}\}", "is_doomsday_planet = yes"]
    targets4[
        r"\b(?:is_gestalt = (?:yes|no)\s+is_(?:machine|hive)_empire = (?:yes|no)|is_(?:machine|hive)_empire = (?:yes|no)\s+is_gestalt = (?:yes|no))"
    ] = [
        r"(?:is_gestalt = (yes|no)\s+is_(?:machine|hive)_empire = \1|is_(?:machine|hive)_empire = (yes|no)\s+is_gestalt = \2)",
        r"is_gestalt = \1\2",
    ]
    targets4[
        r"\b(?:is_fallen_empire = yes\s+is_machine_empire|is_machine_empire = yes\s+is_fallen_empire|is_fallen_machine_empire) = yes"
    ] = "is_fallen_empire_machine = yes"
    targets4[
        r"\b(?:is_fallen_empire = yes\s+has_ethic = ethic_fanatic_(?:%s)|has_ethic = ethic_fanatic_(?:%s)\s+is_fallen_empire = yes)"
        % (VANILLA_ETHICS, VANILLA_ETHICS)
    ] = [
        r"(?:is_fallen_empire = yes\s+has_ethic = ethic_fanatic_(%s)|has_ethic = ethic_fanatic_(%s)\s+is_fallen_empire = yes)"
        % (VANILLA_ETHICS, VANILLA_ETHICS),
        r"is_fallen_empire_\1\2 = yes",
    ]

    targets4[
        r'\b(?:host_has_dlc = "Synthetic Dawn Story Pack"\s*has_machine_age_dlc = (?:yes|no)|has_machine_age_dlc = (?:yes|no)\s*host_has_dlc = "Synthetic Dawn Story Pack")'
    ] = [
        r'(?:host_has_dlc = "Synthetic Dawn Story Pack"\s*has_machine_age_dlc = (yes|no)|has_machine_age_dlc = (yes|no)\s*host_has_dlc = "Synthetic Dawn Story Pack")',
        lambda p: "has_synthetic_dawn_"
        + (
            "not"
            if (not p.group(2) and p.group(1) == "not")
            or (not p.group(1) and p.group(2) == "not")
            else "and"
        )
        + "_machine_age = yes",
    ]
    targets4[r"\n\w+_event = \{\n\s*#[^\n]+"] = [r"(\n\w+_event = \{)\n (#[^\n]+)", ("events", r"\n\2\1")]
    targets3[r"\bNOT = \{\s*any(_\w+ = {)([^{}#]+?)\}\s*\}"] = r"count\1 count = 0 limit = {\2} }"
    targets3[r"\bany(_\w+ = {)\s*\}"] = r"count\1 count > 0 }"
    targets4[r"\bexists = owner\s+can_generate_trade_value = yes"] = "can_generate_trade_value = yes"
    targets4[r"\bfederation = \{\s+any_member = \{\s+[^{}#]+\s+\}"] = [r"\bfederation = \{\s+any_member = \{\s+([^{}#]+)\s+\}", r"any_federation_ally = { \1"]
    targets4[r"\n((\t+)NOT = \{\s+any_\w+ = {(?:[^#\n]+?\s+|(?:\s\t\t\2[^#\n]+?){1,}\s\t\2)\}\n?\2\})\n"] = [r"(\s+)NOT = \{((\1)\s|(\s))any(_\w+ = {)([^#]+)\}(?:\1|\s)\}", r"\1count\5\2count = 0 limit = {\6}\2\3\4}" ]
    targets3[r"\bresource_stockpile_compare = \{\s+resource = (\w+)\s+value\s*([<=>]+\s*\d+)\s+\}"] = r"has_country_resource = { type = \1 amount \2 }"
    # targets4[r"\bresource_stockpile_compare = \{\s+resource = \w+\s+value\s*[<=>]+\s*\d+\s+\}"] = [ r"resource_stockpile_compare = \{\s+resource = (\w+)\s+value\s*([<=>]+\s*\d+)\s+\}", r"has_country_resource = { type = \1 amount \2 }" ]

    # NAND <=> OR = { NOT
    # targets4[r"\s+OR = \{\s*(?:(?:NOT = \{[^{}#]+?|\w+ = \{[^{}#]+? = no)\s+?\}\s+?){2}\s*\}\n"] = [r"OR = \{(\s*)(?:NOT = \{\s*([^{}#]+?)|(\w+ = \{[^{}#]+? = )no)\s+?\}\s+(?:NOT = \{\s*([^{}#]+?)|(\w+ = \{[^{}#]+? = )no)\s+?\}", lambda p: "NAND = {"+p.group(1)+(p.group(2) if isinstance(p.group(2), str) and p.group(2) != "" else p.group(3)+"yes }")+p.group(1)+(p.group(4) if isinstance(p.group(4), str) and p.group(4) != "" else p.group(5)+"yes }")]
    targets4[
        r"((\s+)OR = \{(?:(?:\s+NOT = \{[^\n#]+?\s+?\}|\s+(\w+ = \{)?[^\n#]+? = no(?(3)\s*?\}))){2}\2\})"
    ] = [
        r"OR = \{(\s*)(?:NOT = \{\s*((\w+ = \{)?[^{}#]+?(?(3)\s+?\}))\s+?\}|((\w+ = \{)?[^{}#]+? = )no)(?(5)\s+?\})\s+(?:NOT = \{\s*((\w+ = \{)?[^{}#]+?(?(7)\s+?\}))\s+?\}|((\w+ = \{)?[^{}#]+? = )no)(?(9)\s+?\})",
        lambda p: "NAND = {"
        + p.group(1)
        + (
            p.group(2)
            if p.group(2) and p.group(2) != ""
            else p.group(4) + "yes" + (" }" if p.group(5) and p.group(5) != "" else "")
        )
        + p.group(1)
        + (
            p.group(6)
            if p.group(6) and p.group(6) != ""
            else p.group(8) + "yes" + (" }" if p.group(9) and p.group(9) != "" else "")
        ),
    ]  # NAND = {\1\2\4yes\1\6\8yes

    targets4[r"\b(?:NO[TR] = \{(?:\s+has_trait = trait_(?:hive_mind|mechanical|machine_unit)){3}\s+\})"] = (NO_TRIGGER_FOLDER, "is_valid_pop_for_PLANET_KILLER_NANOBOTS = yes")
    targets4[r"\bcount_\w+ = \{\s+limit = \{[^#]+?\}\s+count\s*[<=>]+\s*[^{}\s]+"] = [r"(count_\w+ = \{)(\s+)(limit = \{[^#]+?\})\2(count\s*[<=>]+\s*[^{}\s]+)", r"\1\2\4\2\3"] # Put count first
    if ACTUAL_STELLARIS_VERSION_FLOAT > 3.99:
        targets4[r"\bpop_amount_percentage = \{\s+limit = \{[^#]+?\}\s+percentage\s*[<=>]+\s*[^{}\s]+"] = [r"(\s+)(limit = \{[^#]+?\})\1(percentage\s*[<=>]+\s*[^{}\s]+)", r"\1\3\1\2"] # Put percentage first
    else:
        targets4[r"\bpop_percentage = \{\s+limit = \{[^#]+?\}\s+percentage\s*[<=>]+\s*[^{}\s]+"] = [r"(pop_percentage = \{)(\s+)(limit = \{[^#]+?\})\2(percentage\s*[<=>]+\s*[^{}\s]+)", r"\1\2\4\2\3"] # Put percentage first

    targets4[
        r"\s+(?:OR = \{)?\s+(?:has_country_flag = synthetic_empire\s+owner_species = \{ has_trait = trait_mechanical \}|owner_species = \{ has_trait = trait_mechanical \}\s+has_country_flag = synthetic_empire)\s+\}?"
    ] = [
        r"(\s+)(\bOR = \{)?(\s+)(?:has_country_flag = synthetic_empire\s+owner_species = \{ has_trait = trait_mechanical \}|owner_species = \{ has_trait = trait_mechanical \}\s+has_country_flag = synthetic_empire)(?(2)\1\})",
        (NO_TRIGGER_FOLDER, r"\1\3is_mechanical_empire = yes"),
    ]
    targets4[
        r"\s+(?:OR = \{)?\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = \"?auth_machine_intelligence\"?)\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = \"?auth_machine_intelligence\"?)\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|has_authority = \"?auth_machine_intelligence\"?)\s+\}?"
    ] = [
        r"(\s+)(OR = \{)?(\s+)(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = \"?auth_machine_intelligence\"?|is_machine_empire = yes))\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = \"?auth_machine_intelligence\"?|is_machine_empire = yes))\s+(?:has_country_flag = synthetic_empire|owner_species = \{ has_trait = trait_mechanical \}|(?has_authority = \"?auth_machine_intelligence\"?|is_machine_empire = yes))(?(2)\1\})",
        (NO_TRIGGER_FOLDER, r"\1\3is_robot_empire = yes"),
    ]
    targets4[
        r"NO[RT] = \{\s*(?:merg_is_(?:fallen_empire|awakened_fe) = yes\s+){2}\}"
    ] = "is_fallen_empire = no"
    targets4[
        r"\s+?(?:OR = \{)?\s+(?:merg_is_(?:fallen_empire|awakened_fe) = yes\s+){2}\}?"
    ] = [
        r"(\s+)(OR = \{)?(?(2)\s+|(\s+))merg_is_(?:fallen_empire|awakened_fe) = yes\s+merg_is_(?:fallen_empire|awakened_fe) = yes(?(2)\s+\})",
        r"\1\3is_fallen_empire = yes",
    ]
    targets4[
        r"\bNO[RT] = \{\s*(?:merg_is_(?:default_empire|awakened_fe) = yes\s+){2}\}"
    ] = "is_country_type_with_subjects = no"
    targets4[
        r"\bOR = \{\s*(?:merg_is_(?:default_empire|awakened_fe) = yes\s+){2}\}"
    ] = "is_country_type_with_subjects = yes"
    targets4[r"\bNO[RT] = \{\s*(?:merg_is_(?:default|fallen)_empire = yes\s+){2}\}"] = (
        "is_default_or_fallen = no"
    )
    targets4[r"\bOR = \{\s*(?:merg_is_(?:default|fallen)_empire = yes\s+){2}\}"] = (
        "is_default_or_fallen = yes"
    )

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def mBox(mtype, text):
    tk.Tk().withdraw()
    style = (
        not mtype
        and messagebox.showinfo
        or mtype == "Abort"
        and messagebox.showwarning
        or messagebox.showerror
    )
    style(title=mtype, message=text)

def iBox(title, prefil):  # , master
    answer = filedialog.askdirectory(
        initialdir=prefil,
        title=title,
        # parent=master
    )
    return answer

# ============== Set paths ===============
def extract_scripted_triggers():
    """
    Scans the mod's 'common/scripted_triggers' directory and extracts the names
    of defined scripted triggers.
    """
    custom_triggers = {}
    triggers_dir = os.path.join(mod_path + "/common/scripted_triggers")
    logger.debug(f"extract_scripted_triggers from: {triggers_dir}")

    if len(triggers_dir) == 0 or not os.path.isdir(triggers_dir):
        logger.debug(f"No 'common/scripted_triggers' directory found in mod at {mod_path}.")
        return custom_triggers

    logger.debug(f"Scanning for scripted triggers in: {triggers_dir}")

    for filepath in glob.glob(triggers_dir + "/*.txt", recursive=False):
        try:
            # Stellaris files often use UTF-8 with BOM, 'utf-8-sig' handles this
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Regex to find trigger names: a_trigger_name = { ... }
                found_in_file = re.findall(r"^([a-zA-Z]\w+) = \{", content, re.MULTILINE)

                if found_in_file:
                    logger.debug(f"Found potential triggers in {filepath}: {found_in_file}")
                    for trigger_name in found_in_file:
                        custom_triggers[trigger_name] = os.path.basename(filepath)
        except Exception as e:
            logger.error(f"Error reading or parsing scripted triggers from {filepath}: {e}")

    logger.info(f"Discovered {len(custom_triggers)} unique custom scripted trigger(s) in the mod.")
    if custom_triggers:
        logger.debug(f"Mod custom triggers: {custom_triggers}")
    return custom_triggers

def merg_planet_rev_lambda(p):
    return {
    "yes": "is_planet_class = pc_" + p.group(1),
    "no": "NOT = { is_planet_class = pc_" + p.group(1) + " }"
    }[p.group(2)]

def apply_merger_of_rules(targets3, targets4, is_subfolder=False):
    """Define the Merger of Rules triggers and check if they exist in the mod.
    --mergerofrules: Enable Merger of Rules compatibility mode.
    This flag forces compatibility logic for mods that use The Merger of Rules. When enabled, the script automatically scans your mod for custom scripted_triggers, and attempts to detect and apply supported MoR triggers individually.
    If a known MoR trigger is present in your mod, it will be converted automatically.
    If a trigger is not found, it will be safely skipped, avoiding unnecessary edits.
    This flag works even if your mod doesn't include the full Merger of Rules — useful for partial adoption or integration.
    """
    tar3 = {}
    tar4 = {}

    merger_triggers = {
        "is_endgame_crisis": (
            r"\b(?:(?:(?:is_country_type = (?:awakened_)?synth_queen(?:_storm)?|is_endgame_crisis = yes)\s*?){2,3}|(?:is_country_type = (?:extradimensional(?:_[23])?|swarm|ai_empire)\s*?){5})",
            (NO_TRIGGER_FOLDER, "is_endgame_crisis = yes"),
            4
        ),
        "merg_is_fallen_empire": (r"\bis_country_type = fallen_empire\b", (NO_TRIGGER_FOLDER, "merg_is_fallen_empire = yes")),
        "merg_is_awakened_fe": (r"\bis_country_type = awakened_fallen_empire\b", (NO_TRIGGER_FOLDER, "merg_is_awakened_fe = yes")),
        "merg_is_hab_ringworld": (r"\b(is_planet_class = pc_ringworld_habitable\b|uses_district_set = ring_world\b|is_planetary_diversity_ringworld = yes|is_giga_ringworld = yes)" , (NO_TRIGGER_FOLDER, "merg_is_hab_ringworld = yes")),
        "merg_is_hive_world": (r"\b(is_planet_class = pc_hive\b|is_pd_hive_world = yes)", (NO_TRIGGER_FOLDER, "merg_is_hive_world = yes", )),
        "merg_is_relic_world": (r"\bis_planet_class = pc_relic\b", (NO_TRIGGER_FOLDER, "merg_is_relic_world = yes")),
        "merg_is_machine_world": (r"\b(is_planet_class = pc_machine\b|is_pd_machine = yes)", (NO_TRIGGER_FOLDER, "merg_is_machine_world = yes")),
        "merg_is_habitat": (r"\b(is_planet_class = pc_habitat|is_pd_habitat = yes)\b", (NO_TRIGGER_FOLDER, "merg_is_habitat = yes")),
        "merg_is_molten": (r"is_planet_class = pc_molten\b", (NO_TRIGGER_FOLDER, r"merg_is_molten = yes")),
        "merg_is_toxic": (r"is_planet_class = pc_toxic\b", (NO_TRIGGER_FOLDER, r"merg_is_toxic = yes")),
        "merg_is_frozen": (r"is_planet_class = pc_frozen\b", (NO_TRIGGER_FOLDER, r"merg_is_frozen = yes")),
        "merg_is_barren": (r"is_planet_class = pc_barren\b", (NO_TRIGGER_FOLDER, r"merg_is_barren = yes")),
        "merg_is_barren_cold": (r"is_planet_class = pc_barren_cold\b", (NO_TRIGGER_FOLDER, r"merg_is_barren_cold = yes")),
        "merg_is_gaia_basic": (r"\b(is_planet_class = pc_gaia|pd_is_planet_class_gaia = yes)\b", (NO_TRIGGER_FOLDER, r"merg_is_gaia_basic = yes")),
        "merg_is_arcology": (r"\b(is_planet_class = pc_city\b|is_pd_arcology = yes|is_city_planet = yes)" , (NO_TRIGGER_FOLDER, "merg_is_arcology = yes")),
    }
    if not keep_default_country_trigger:
        merger_triggers["merg_is_default_empire"] = (r"\bis_country_type = default\b", (NO_TRIGGER_FOLDER, "merg_is_default_empire = yes"))

    if mergerofrules:
        for trigger in merger_triggers:
            if len(merger_triggers[trigger]) == 3:
                tar4[merger_triggers[trigger][0]] = merger_triggers[trigger][1]
            else:
                tar3[merger_triggers[trigger][0]] = merger_triggers[trigger][1]
        if not keep_default_country_trigger:
            tar4[
                r"\s(?:%s)_playable_country = \{[^{}#]*(?:limit = \{\s+)?(?:is_country_type = default|CmtTriggerIsPlayableEmpire = yes|is_zofe_compatible = yes|merg_is_default_empire = yes)\s*" % VANILLA_PREFIXES] = [
                r"((?:%s)_playable_country = \{[^{}#]*?(?:limit = \{\s+)?)(?:is_country_type = default|CmtTriggerIsPlayableEmpire = yes|is_zofe_compatible = yes|merg_is_default_empire = yes)\s*" % VANILLA_PREFIXES, r"\1",
            ]
            # without is_country_type_with_subjects & without is_fallen_empire = yes
            tar4[
                r"\b(?:(?:(?:is_country_type = default|merg_is_default_empire = yes)\s+(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes))|(?:(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)\s+(?:is_country_type = default|merg_is_default_empire = yes))|(?:(?:is_country_type = default|merg_is_default_empire = yes)\s+(is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)\s+(?:is_country_type = fallen_empire|merg_is_fallen_empire = yes)))"
            ] = [
                r"\b((?:is_country_type = default|merg_is_default_empire = yes|is_country_type = fallen_empire|merg_is_fallen_empire = yes|is_country_type = awakened_fallen_empire|merg_is_awakened_fe = yes)(\s+)){2,}",
                (NO_TRIGGER_FOLDER, r"is_default_or_fallen = yes\2"),
            ]
    elif not is_subfolder:
        triggers_in_mod = extract_scripted_triggers()
        merger_reverse_triggers = {
            "merg_is_default_empire": (r"\bmerg_is_default_empire = (yes|no)", lambda p: {"yes": "is_country_type = default", "no": "NOT = { is_country_type = default }"}[p.group(1)] ),
            "merg_is_fallen_empire": (r"\bmerg_is_fallen_empire = (yes|no)", lambda p: {"yes": "is_country_type = fallen_empire", "no": "NOT = { is_country_type = fallen_empire }"}[p.group(1)] ),
            "merg_is_awakened_fe": (r"\bmerg_is_awakened_fe = (yes|no)", lambda p: {"yes": "is_country_type = awakened_fallen_empire", "no": "NOT = { is_country_type = awakened_fallen_empire }"}[p.group(1)] ),
            "merg_is_hab_ringworld": ( r"\bmerg_is_hab_ringworld = (yes|no)", r"has_ringworld_output_boost = \1" ),
            "merg_is_hive_world": ( r"\bmerg_is_(hive)_world = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_relic_world": ( r"\bmerg_is_(relic)_world = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_machine_world": ( r"\bmerg_is_(machine)_world = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_habitat": ( r"\bmerg_is_(habitat) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_molten": ( r"\bmerg_is_(molten) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_toxic": ( r"\bmerg_is_(toxic) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_frozen": ( r"\bmerg_is_(frozen) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_barren": ( r"\bmerg_is_(barren) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_barren_cold": ( r"\bmerg_is_(barren_cold) = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_gaia_basic": ( r"\bmerg_is_(gaia)_basic = (yes|no)", merg_planet_rev_lambda ),
            "merg_is_arcology": ( r"\bmerg_is_arcology = (yes|no)", lambda p: {"yes": "is_planet_class = pc_city", "no": "NOT = { is_planet_class = pc_city }"}[p.group(1)] ),
        }

        for trigger in merger_triggers:
            if trigger in triggers_in_mod:
                if len(merger_triggers[trigger]) == 3:
                    # Filename, replace pattern
                    tar4[merger_triggers[trigger][0]] = { triggers_in_mod[trigger]: merger_triggers[trigger][1][1] }  # merger_triggers[trigger][1]
                else:
                    tar3[merger_triggers[trigger][0]] = { triggers_in_mod[trigger]: merger_triggers[trigger][1][1] }  # merger_triggers[trigger][1]

                logger.debug(f"Enabling conversion for MoR trigger: {trigger}")
            elif trigger in merger_reverse_triggers:
                tar3[merger_reverse_triggers[trigger][0]] = merger_reverse_triggers[trigger][1]
                logger.debug(f"Removing nonexistent MoR trigger: {trigger}")

    ### Pre-Compile regexps
    tar3 = [(re.compile(k, flags=0), tar3[k]) for k in tar3]
    tar4 = [(re.compile(k, flags=re.I), tar4[k]) for k in tar4]
    # print(tar3)
    # print(tar4)
    targets3.extend(tar3)
    targets4.extend(tar4)

    return (targets3, targets4)

def parse_dir():
    global mod_path, mod_outpath, log_file, start_time #, targets3, targets4

    files = []
    mod_path = os.path.normpath(mod_path)

    print(f"Welcome to Stellaris Mod-Updater-{FULL_STELLARIS_VERSION} by FirePrince!")

    if not os.path.isdir(mod_path) or not os.path.isfile(os.path.join(mod_path, "descriptor.mod")):
        mod_path = os.getcwd() if not os.path.isdir(mod_path) else mod_path
        mod_path = iBox("Please select a mod folder:", mod_path)

    if not os.path.isdir(mod_path):
        # except OSError:
        #   print('Unable to locate the mod path %s' % mod_path)
        mBox("Error", "Unable to locate the mod path %s" % mod_path)
        return False
    if (
        len(mod_outpath) < 1
        or not os.path.isdir(mod_outpath)
        or mod_outpath == mod_path
    ):
        mod_outpath = mod_path
        if only_warning:
            print("Attention: files are ONLY checked!")
        else:
            print("Warning: Mod files will be overwritten!")
    else:
        mod_outpath = os.path.normpath(mod_outpath)

    # Using the custom formatter
    # Prevent adding multiple handlers if this setup code is run more than once
    if logger.handlers or logger.hasHandlers():
        logging.debug("Logger handler already exists")
        logger.handlers.clear()

    # Create a handler for sys.stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(SafeFormatter('%(levelname)s - %(message)s'))

    def add_logfile_handler():
        global log_file
        if log_file and log_file != "":
            # Open the log file in append mode
            # print(f"mod_outpath: {mod_outpath}, log_file: {log_file}")
            log_file = os.path.join(mod_outpath, log_file)
            if os.path.exists(log_file):
                os.remove(log_file)
            # log_file = open(log_file, "w", encoding="utf-8", errors="ignore")
            # Create a handler for your existing log_file object
            log_file = logging.FileHandler(log_file, mode='a', encoding='utf-8', errors='replace')
            # We use StreamHandler because log_file is an already open file stream
            # log_file = logging.StreamHandler(log_file)
            log_file.setLevel(logging.DEBUG)
            log_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(log_file)

    logger.addHandler(stdout_handler)

    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logging.debug("\tLoading folder %s" % mod_path)
    start_time = datetime.datetime.now()

    # if os.path.isfile(mod_path + os.sep + 'descriptor.mod'):
    if os.path.exists(os.path.join(mod_path, "descriptor.mod")):
        # files = glob.glob(mod_path + "/**", recursive=True)  # '\\*.txt'
        files = glob.glob(mod_path + "/common/**", recursive=True)
        files.extend(glob.glob(mod_path + "/events/*.txt", recursive=False))
        add_logfile_handler()
        modfix(files)
    else:
        # "We have a main or a sub folder"
        # folders = [f for f in os.listdir(mod_path) if os.path.isdir(os.path.join(mod_path, f))]
        folders = glob.iglob(mod_path + "/*/", recursive=False)
        basename = os.path.basename(mod_path)
        # print(basename)
        # print(list(folders))
        if basename == "common" or next(folders, -1) == -1:
            files = glob.glob(mod_path + "/**", recursive=True)  # '\\*.txt'
            # print(files)
            if (
                not files
                or not isinstance(files, list)
                or len(files) < 2
            ):
                # print("# Empty folder", mod_path, file=log_file)
                logger.warning("Empty folder %s." % mod_path)
            else:
                # print("# We have clear a sub-folder", file=log_file)
                logger.warning("We have clear a sub-folder.")
                outpath = ""
                if "common/" in mod_path:
                    outpath = mod_path.split("common/")
                    if len(outpath) > 1:
                        outpath, basename = outpath
                        basename = f"common/{basename}"
                    else:
                        outpath = outpath[0]
                else:
                    outpath, basename = os.path.split(mod_path)

                if mod_outpath == mod_path:
                    mod_outpath = outpath
                    logger.warning(f"New output folder {mod_outpath}")

                add_logfile_handler()
                modfix(files, basename)
        else:
            add_logfile_handler()
            logger.debug("We have a main-folder?")
            for _f in folders:
                if os.path.exists(os.path.join(_f, "descriptor.mod")):
                    mod_path = _f
                    mod_outpath = os.path.join(mod_outpath, _f)
                    # print(mod_path, file=log_file)
                    logger.info(mod_path)
                    # files = glob.glob(mod_path + "/**", recursive=True)  # '\\*.txt'
                    files = glob.glob(mod_path + "/common/**", recursive=True)
                    files.extend(glob.glob(mod_path + "/events/*.txt", recursive=False))
                    modfix(files)
                else:
                    # files = glob.glob(mod_path + "/**", recursive=True)  # '\\*.txt'
                    files = glob.glob(mod_path + "/common/*.txt", recursive=True)
                    files.extend(glob.glob(mod_path + "/events/*.txt", recursive=False))
                    if next(iter(files), -1) != -1:
                        # print("# We have probably a mod sub-folder", file=log_file)
                        logger.warning("We have probably a mod sub-folder")
                        modfix(files)

def modfix(file_list, is_subfolder=False):
    logging.debug(f"mod_path: {mod_path}\nmod_outpath: {mod_outpath}\nfile_list: {file_list}")

    tar3, tar4 = apply_merger_of_rules(list(targets3), list(targets4), is_subfolder)

    # logging.debug(f"len tar3={len(tar3)} len tar3={len(tar3)}")
    subfolder = ""

    for _file in file_list:
        if os.path.isfile(_file) and _file.endswith(".txt"):
            file_contents = ""
            logging.debug("\tCheck file: %s" % _file)
            with open(_file, "r", encoding="utf-8", errors="ignore") as txtfile:
                # out = txtfile.read() # full_fille
                # try:
                # print(_file, type(_file))
                # pattern = re.compile(u)
                # print(pattern.search(txtfile))
                # for t, r in targets2.items():
                #   targets = re.findall(t, txtfile)
                #   if len(targets) > 0:
                #       for target in targets:
                #           value = target.split("=")[1]
                #           replacer = ""
                #           for i in range(len(r)):
                #               replacer += r[i]
                #               if i < len(r) -1:
                #                   replacer += value
                #           if target in line and replacer not in line:
                #               line = line.replace(target,replacer)

                file_contents = txtfile.readlines()
                if is_subfolder:
                    basename = _file
                    subfolder = is_subfolder
                else:
                    subfolder = os.path.relpath(_file, mod_path)
                    subfolder, basename = os.path.split(subfolder)

                subfolder = subfolder.replace("\\", "/")
                # print(f"subfolder '{subfolder}', basename '{basename}'")
                out = ""
                changed = False
                # Since v4.0
                if ACTUAL_STELLARIS_VERSION_FLOAT > 3.99 and any(subfolder.startswith(ef) for ef in EFFECT_FOLDERS):
                    file_contents, changed = transform_add_trait(basename, file_contents, changed)

                for i, line in enumerate(file_contents):
                    stripped = line.strip()
                    if len(stripped) > 8 and not stripped.startswith("#"):
                        # for line in file_contents:
                        # if subfolder in "prescripted_countries":
                        #   print(stripped.encode(errors='replace'))
                        for rt in targetsR:
                            # if not isinstance(rt, list) or not len(rt) > 1: logger.warning(rt) else:
                            rt, msg = rt

                            if isinstance(msg, tuple):
                                folder, msg = msg
                                # print(type(subfolder), subfolder, folder)
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            folder = False
                                            break
                                    if folder:
                                        rt = False
                                elif isinstance(folder, str):
                                    if subfolder not in folder:
                                        rt = False
                                elif isinstance(folder, re.Pattern):
                                    if not folder.search(subfolder):
                                        rt = False
                                else: rt = False

                            if rt:
                                # rt = re.search(rt, stripped)  # , flags=re.I
                                rt = rt.search(stripped)
                            if rt:
                                # print(
                                #     "# WARNING: Potentially deprecated Syntax (%s): %s in line %i file %s\n"
                                #     % (
                                #         msg,
                                #         rt.group(0),
                                #         i,
                                #         basename,
                                #     ),
                                #     file=log_file,
                                #
                                # )
                                logger.warning(
                                    "Potentially deprecated Syntax (%s): %s in line %i file %s\n"
                                    % (
                                        msg,
                                        rt.group(0),
                                        i,
                                        basename,
                                    )
                                )
                                break # just one hit per line

                        # for pattern, repl in tar3.items(): old dict way
                        for pattern in tar3:  # new list way
                            repl = pattern[1]
                            pattern = pattern[0] # id
                            folder = None
                            # check valid folder
                            rt = False
                            # File name check
                            if isinstance(repl, dict):
                                # is a 3 tuple
                                file, repl = list(repl.items())[0]
                                if debug_mode:
                                    print("tar3", stripped, "\n", pattern, repl, file)
                                if isinstance(repl, str):
                                    if file != basename:
                                        rt = True
                                elif file in basename:
                                    if debug_mode:
                                        print("\tFILE match:", file, basename)
                                    folder, repl, rt = repl
                                else:
                                    folder, rt, repl = repl
                                if folder:
                                    if isinstance(folder, list):
                                        # print("folder list", subfolder, folder)
                                        for fo in folder:
                                            if subfolder in fo:
                                                rt = True
                                                # print("folder matches", subfolder, folder)
                                    elif subfolder in folder:
                                        rt = True
                                    else:
                                        rt = False
                            # Folder check
                            elif isinstance(repl, tuple):
                                folder, repl = repl
                                # logging.debug("subfolder", subfolder, folder)
                                if isinstance(folder, list):
                                    # print("folder list", subfolder, folder)
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                            # print("folder matches", subfolder, folder)
                                # elif subfolder in folder:
                                elif isinstance(folder, str):
                                    # logging.debug("subfolder in folder", subfolder, folder)
                                    if subfolder in folder:
                                        rt = True
                                        # logging.debug(folder)
                                elif isinstance(folder, re.Pattern):
                                    if folder.search(subfolder):
                                        # logging.debug("Check folder (regexp) True", subfolder, repl)
                                        rt = True
                                    # ellogging.debug("Folder EXCLUDED:", subfolder, repl)
                                else:
                                    rt = False

                            else:
                                rt = True
                            if rt:  # , flags=re.I # , count=0, flags=0
                                match = pattern.search(line)  # , flags=re.I
                                if match:
                                    rt = line
                                    line = pattern.sub(repl, rt, count=1)  # , flags=re.I
                                    # line = line.replace(t, r)
                                    if line != rt:
                                        changed = True
                                        # print( "\t# Updated file: %s on %s (at line %i) with %s\n" % ( basename, rt.strip(), i, stripped, ), file=log_file, )
                                        logger.info(
                                            "\tUpdated file: %s on %s (at line %i) with %s\n"
                                            % (
                                                basename,
                                                rt.lstrip(),
                                                i,
                                                line.lstrip(),
                                            )
                                        )
                                        # Determine the span of the match
                                        match_start, rt = match.span()
                                        # Check if the match spans the entire line (excluding leading/trailing whitespace)
                                        if match_start <= 6 and rt >= len(stripped) - 6:
                                            print("The entire line is matched; no further matches possible")
                                            break  # The entire line is matched; no further matches possible
                                # elif debug_mode and isinstance(folder, re.Pattern): print("DEBUG Match "tar3":", pattern, repl, type(repl), stripped.encode(errors='replace'))

                    out += line

                if "inline_scripts" not in subfolder:
                    # The last values from the loop
                    if line[-1][0] != "\n" and not stripped.startswith("#"):
                        out += "\n"
                        logger.info("Added needed empty line at end.", i, line, len(line))
                        changed = True
                    if out.startswith('\n'):
                        out = out.replace('\n', '', 1)
                        changed = True

                # for pattern, repl in tar4.items(): old dict way
                for pattern in tar4:  # new list way
                    repl = pattern[1]
                    pattern = pattern[0]
                    targets = pattern.findall(out)
                    if targets and len(targets) > 0:
                        # logger.debug("tar4", targets, type(targets))
                        for tar in targets:
                            # check valid folder
                            rt = False
                            replace = repl
                            if isinstance(repl, list) and isinstance(repl[1], tuple):
                                # logging.debug('Has folder check')
                                replace = repl.copy()
                                # folder = repl[1][0]
                                # replace[1] = repl[1][1]
                                folder, replace[1] = repl[1]
                                rt = False
                                if debug_mode:
                                    logger.debug(type(replace), replace, replace[1])
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                            if debug_mode:
                                                print(folder)
                                            break
                                elif isinstance(folder, str):
                                    if subfolder in folder:
                                        rt = True
                                        # logging.debug(folder)
                                elif isinstance(folder, re.Pattern) and folder.search(
                                    subfolder
                                ):
                                    # print("Check folder (regexp)", subfolder)
                                    rt = True
                                else:
                                    rt = False
                            elif isinstance(repl, tuple):
                                # logging.debug('Has folder check simple')
                                folder, replace = repl
                                # logging.debug("subfolder", subfolder, folder)
                                if isinstance(folder, list):
                                    for fo in folder:
                                        if subfolder in fo:
                                            rt = True
                                # elif subfolder in folder:
                                elif isinstance(folder, str):
                                    # logging.debug("subfolder in folder", subfolder, folder)
                                    if subfolder in folder:
                                        rt = True
                                        # logging.debug(folder)
                                elif isinstance(folder, re.Pattern):
                                    if folder.search(subfolder):
                                        # logging.debug("Check folder (regexp) True", subfolder, repl)
                                        rt = True
                                    # ellogging.debug("Folder EXCLUDED:", subfolder, repl)
                                else:
                                    rt = False
                            elif isinstance(repl, dict): # Trigger filename
                                file, replace = list(repl.items())[0]
                                # print(pattern, file, type(file), replace, type(basename))
                                if file != basename:
                                    rt = True
                                # else: print("\tEXCLUDED:", pattern, "from", basename)
                            else:
                                rt = True
                            if rt:
                                # print(type(repl), tar, type(tar), subfolder)
                                if isinstance(repl, list):
                                    if isinstance(tar, tuple):
                                        tar = tar[0]  # Take only first group
                                        if debug_mode:
                                            print("ONLY GRP1:", type(replace), replace)
                                    replace = re.sub(
                                        replace[0],
                                        replace[1],
                                        tar,
                                        count=1,
                                        flags=re.I | re.M | re.A,
                                    )
                                if isinstance(repl, str) or (
                                    not isinstance(tar, tuple)
                                    and tar in out
                                    and tar != replace
                                ):
                                    # print("# Match:\n", tar, file=log_file)
                                    # print("Match:\n", tar, file=sys.stdout)
                                    logger.info("Match:\n %s" % tar)
                                    if isinstance(tar, tuple):
                                        tar = tar[0]  # Take only first group
                                        logger.debug(f"\tFROM GROUP1:\n{pattern}")
                                    elif debug_mode:
                                        logger.debug("\tFROM:\n", pattern)
                                    # print("# Multiline replace:\n", replace, file=log_file)
                                    # print("Multiline replace:\n", replace, file=sys.stdout)
                                    logger.info("Multiline replace:\n%s" % replace)
                                    out = out.replace(tar, replace)
                                    changed = True
                                elif debug_mode:
                                    logger.debug(f"DEBUG BLIND MATCH: {tar} {repl} {type(repl)} {replace}")

                if changed and not only_warning:
                    structure = os.path.normpath(os.path.join(mod_outpath, subfolder))
                    out_file = os.path.join(structure, basename)
                    # print("\t# WRITE FILE:", out_file, file=log_file, )
                    logger.info("\tWRITE FILE: %s" % out_file)
                    if not os.path.exists(structure):
                        os.makedirs(structure)
                        # print('Create folder:', subfolder)
                    open(out_file, "w", encoding="utf-8").write(out)

                # except Exception as e:
                # except OSError as e:
                #   print(e)
                #   print("Unable to open", _file)
            txtfile.close()
        # elif os.path.isdir(_file):
        #   # if .is_dir():
        #   # subfolder = _file.replace(mod_path + os.path.sep, '')
        #   subfolder = os.path.relpath(_file, mod_path)
        #   # print("subfolder:", subfolder)
        #   structure = os.path.join(mod_outpath, subfolder)
        #   if not os.path.isdir(structure):
        #       os.mkdir(structure)
        # else: print("NO TXT?", _file)

    logger.info(f"✅ Script completed in {(datetime.datetime.now() - start_time).total_seconds():.2f} seconds")

    ## Update mod descriptor
    _file = os.path.join(mod_path, "descriptor.mod")
    if not only_warning and os.path.exists(_file):
        with open(_file, "r", encoding="utf-8", errors="ignore") as descriptor_mod:
            # out = descriptor_mod.readlines()
            out = descriptor_mod.read()
            main_ver_len = FULL_STELLARIS_VERSION.rfind(".")
            new_main_ver = FULL_STELLARIS_VERSION[0:main_ver_len]

            # Main Version = 4.0 (main_ver_len = 3)
            logger.info(
                r"Main Version = %s (Sub-version = %s)"
                % (new_main_ver, FULL_STELLARIS_VERSION[main_ver_len:])
            )
            # Game version
            pattern = re.compile(r'supported_version="v?(.*?)"')
            m = pattern.search(out) # old game version
            if m: m = m.group(1)
            logging.debug(m, isinstance(m, str), len(m))

            if isinstance(m, str) and m != FULL_STELLARIS_VERSION:
                old_ver_len = m.rfind(".")
                old_main_ver = m[0:old_ver_len]

                if old_main_ver != new_main_ver:
                    if m.endswith("*"):
                        out = re.sub(
                            pattern,
                            r'supported_version="v%s"'
                            % (FULL_STELLARIS_VERSION[0 : main_ver_len + 1] + "*"),
                            out,
                            count=1
                        )
                    else:
                        out = re.sub(
                            pattern, r'supported_version="v%s"' % FULL_STELLARIS_VERSION,
                            out,
                            count=1
                        )
                    if debug_mode:
                        print(
                            type(out),
                            out.encode("utf-8", errors="replace"),
                            old_main_ver,
                            new_main_ver,
                        )
                # Mod version
                pattern = re.compile(r'\bversion="v?(.*?)"(?=\n)')
                m = pattern.search(out) # old mod version
                if m:
                    m = m.group(1)
                    print("Old Mod-version = %s" % m)
                    if re.search(r"\.\d+$", m):
                        if  (
                            m.startswith(old_main_ver) and old_main_ver != new_main_ver
                            or m.startswith(new_main_ver) and m.replace(r"\.\d+$", "") != FULL_STELLARIS_VERSION
                        ):
                            out = pattern.sub(r'version="%s"' % (FULL_STELLARIS_VERSION + ".0"), out, count=1)
                        elif m.replace(r"\.\d+$", "") != FULL_STELLARIS_VERSION:
                            # print(m, FULL_STELLARIS_VERSION, len(FULL_STELLARIS_VERSION))
                            out = out.replace(m, FULL_STELLARIS_VERSION + ".0")
                            out = out.replace(old_main_ver, FULL_STELLARIS_VERSION)
                    else: print("No proper mod version found", re.search(r"\.\d+$", m))
                else: print("No mod version exists")
                # Mod name
                pattern_name = re.compile(r'name="(.*?)"\n')
                pattern = pattern_name.search(out)
                if pattern:
                    pattern = pattern.group(1)

                # b'Freebooters Origin [3.14.\xe2\x98\xa0] (reborn)' version 3.14.1592653.0 on 'descriptor.mod' updated to 4.0.5!
                # print(
                #     pattern,
                #     "version %s on 'descriptor.mod' updated to %s!"
                #     % (m, FULL_STELLARIS_VERSION),
                #     file=log_file,
                # )
                logger.info(
                    "%s version %s on 'descriptor.mod' updated to %s!"
                    % (pattern, m, FULL_STELLARIS_VERSION)
                )
                if isinstance(pattern, str) and old_main_ver != new_main_ver and re.search(old_main_ver, pattern):
                    out = out.replace(pattern, pattern.replace(old_main_ver, new_main_ver))
                # Since 3.12 there is a "v" prefix for version
                # FULL_STELLARIS_VERSION = re.compile(r'supported_version=\"v')
                if not re.search('supported_version="v', out):
                    out = out.replace('supported_version="', 'supported_version="v')
                open(_file, "w", encoding="utf-8", errors="ignore").write(out.strip())

    # print("\n# Done!", mod_outpath, file=log_file)
    logger.info("✅ Done! %s" % mod_outpath)

class SafeFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        # Only sanitize non-printables directly in the str
        return message.encode('utf-8', errors='replace').decode('utf-8')

if __name__ == "__main__":
    # Configure basic logging - this can be overridden by argparse later
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s' )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)       # Ensure all levels pass through
    logger.propagate = False             # Prevent double logging

    args = parse_arguments()

    if args.mod_path: mod_path = args.mod_path
    if args.only_warning: only_warning = args.only_warning
    if args.only_actual: only_actual = args.only_actual
    if args.code_cosmetic: code_cosmetic = args.code_cosmetic
    if args.also_old: also_old = args.also_old
    if args.debug_mode: debug_mode = args.debug_mode
    if args.mergerofrules: mergerofrules = args.mergerofrules
    if args.keep_default_country_trigger: keep_default_country_trigger = args.keep_default_country_trigger

    setBoolean(only_warning)
    setBoolean(code_cosmetic)
    setBoolean(only_actual)
    setBoolean(also_old)
    setBoolean(debug_mode)
    setBoolean(mergerofrules)
    setBoolean(keep_default_country_trigger)

    if mod_path and mod_path != "":
        mod_path = os.path.normpath(mod_path)
    if (
        mod_path is None
        or mod_path == ""
        or not os.path.exists(mod_path)
        or not os.path.isdir(mod_path)
        ):
        if os.path.exists(
            os.path.expanduser("~") + "/Documents/Paradox Interactive/Stellaris/mod"
        ):
            mod_path = (
                os.path.expanduser("~") + "/Documents/Paradox Interactive/Stellaris/mod"
            )
        else:
            CSIDL_PERSONAL = 5
            SHGFP_TYPE_CURRENT = 0
            temp = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, temp
            )
            mod_path = temp.value + "/Paradox Interactive/Stellaris/mod"

    start_time = 0
    # exit()

    # 3. Main logic
    if only_actual:
        # If only_actual is True, find the highest applicable version and apply its data.
        # Then, stop.
        for version_threshold, data_dict in version_data_sources:
            if ACTUAL_STELLARIS_VERSION_FLOAT >= version_threshold:
                _apply_version_data_to_targets(data_dict)
                break  # Processed the highest matching version, so exit loop
    else:
        # If only_actual is False, apply data from all applicable versions.
        # This replicates the cumulative behavior of your original if statements.
        for version_threshold, data_dict in version_data_sources:
            if ACTUAL_STELLARIS_VERSION_FLOAT >= version_threshold:
                _apply_version_data_to_targets(data_dict)

    targetsR = actuallyTargets["targetsR"]
    targets3 = actuallyTargets["targets3"]
    targets4 = actuallyTargets["targets4"]

    if also_old:
        ## 2.0
        # planet trigger fortification_health was removed
        ## 2.2
        targets3[r"(\s*)planet_unique = yes"] = ("common/buildings", r"\1base_cap_amount = 1")
        targets3[r"(\s*)empire_unique = yes"] = ("common/buildings", r"\1empire_limit = { base = 1 }")
        targets3[r"(\s*)is_listed = no"] = ("common/buildings", r"\1can_build = no")
        targets3[r"\s+(?:outliner_planet_type|tile_set) = \w+\s*"] = ("common/planet_classes", "")
        targets3[r"\b(?:add|set)_blocker = \"?tb_(\w+)\"?"] = (
            r"add_deposit = d_\1"  # More concrete? r"add_blocker = { type = d_\1 blocked_deposit = none }"
        )
        targets3[r"\btb_(\w+)"] = r"d_\1"
        targets3[r"\b(building_capital)(?:_\d)\b"] = r"\1"
        targets3[r"\b(betharian_power_plant)\b"] = r"building_\1"
        targets3[r"\b(building_hydroponics_farm)_[12]\b"] = r"\1"
        targets3[r"\bbuilding_hydroponics_farm_[34]\b"] = "building_food_processing_facility"
        targets3[r"\bbuilding_hydroponics_farm_[5]\b"] = "building_food_processing_center"
        targets3[r"\bbuilding_power_plant_[12]\b"] = "building_energy_grid"
        targets3[r"\bbuilding_power_plant_[345]\b"] = "building_energy_nexus"
        targets3[r"\bbuilding_mining_network_[12]\b"] = "building_mineral_purification_plant"
        targets3[r"\bbuilding_mining_network_[345]\b"] = "building_mineral_purification_hub"
        # TODO needs more restriction
        # targets3[r"(?<!add_resource = \{)(\s+)(%s)\s*([<=>]+\s*-?\s*(?:@\w+|\d+))\1(?!(%s))" % (RESOURCE_ITEMS, RESOURCE_ITEMS)] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1has_resource = { type = \2 amount \3 }")
        # Unknown old version
        targets3[r"\bcountry_resource_(influence|unity)_"] = r"country_base_\1_produces_"
        targets3[r"\bplanet_unrest_add"] = "planet_stability_add"
        targets3[r"\bshipclass_military_station_hit_points_"] = "shipclass_military_station_hull_"
        targets3[r"(.+?)\sorbital_bombardment = (\w{4:})"] = (
            r"\1has_orbital_bombardment_stance = \2"  # exclude country_type option
        )
        targets3[r"\bNAME_Space_Amoeba\b"] = "space_amoeba"
        targets3[r"\btech_spaceport_(\d)\b"] = r"tech_starbase_\1"
        targets3[r"\btech_mining_network_(\d)\b"] = r"tech_mining_\1"
        targets3[r"\bgarrison_health\b"] = r"army_defense_health_mult"
        targets3[r"\bplanet_jobs_minerals_mult\b"] = "planet_jobs_minerals_produces_mult"
        targets3[r"country_flag = flesh_weakened\b"] = "country_flag = cyborg_empire"
        targets3[r"\bhas_government = ([^g][^o][^v])"] = r"has_government = gov_\1"
        targets3[r"\bgov_ordered_stratocracy\b"] = "gov_citizen_stratocracy"
        targets3[r"\bgov_military_republic\b"] = "gov_military_commissariat"
        targets3[r"\bgov_martial_demarchy\b"] = "gov_martial_empire"
        targets3[r"\bgov_pirate_codex\b"] = "gov_pirate_haven"
        targets3[r"\bgov_divine_mandate\b"] = "gov_divine_empire"
        targets3[r"\bgov_transcendent_empire\b"] = "gov_theocratic_monarchy"
        targets3[r"\bgov_transcendent_republic\b"] = "gov_theocratic_republic"
        targets3[r"\bgov_transcendent_oligarchy\b"] = "gov_theocratic_oligarchy"
        targets3[r"\bgov_irenic_democracy\b"] = "gov_moral_democracy"
        targets3[r"\bgov_indirect_democracy\b"] = "gov_representative_democracy"
        targets3[r"\bgov_democratic_utopia\b"] = "gov_direct_democracy"
        targets3[r"\bgov_stagnated_ascendancy\b"] = "gov_stagnant_ascendancy"
        targets3[r"\bgov_peaceful_bureaucracy\b"] = "gov_irenic_bureaucracy"
        targets3[r"\bgov_irenic_protectorate\b"] = "gov_irenic_dictatorship"
        targets3[r"\bgov_mega_corporation\b"] = "gov_megacorporation"
        targets3[r"\bgov_primitive_feudalism\b"] = "gov_feudal_realms"
        targets3[r"\bgov_fragmented_nations\b"] = "gov_fragmented_nation_states"
        targets3[r"\bgov_illuminated_technocracy\b"] = "gov_illuminated_autocracy"
        targets3[r"\bgov_subconscious_consensus\b"] = "gov_rational_consensus"
        targets3[r"\bgov_ai_overlordship\b"] = "gov_despotic_hegemony"
        # not sure because multiline
        # targets3[r"(?<!add_resource = \{)(\s+)(%s)\s*([<=>]+\s*-?\s*(?:@\w+|\d+))" % RESOURCE_ITEMS] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1has_resource = { type = \2 amount \3 }")
        # tmp fix
        # targets3[r"\bhas_resource = \{ type = (%s) amount( = (?:\d+|@\w+)) \}" % RESOURCE_ITEMS] = (["common/scripted_triggers", "common/scripted_effects", "events"], r"\1\2 ")

    if code_cosmetic and not only_warning:
        do_code_cosmetic()

    ### Pre-Compile regexps
    targets3 = [(re.compile(k, flags=0), targets3[k]) for k in targets3]
    targets4 = [(re.compile(k, flags=re.I), targets4[k]) for k in targets4]
    # targetsR = [(re.compile(k[0], flags=0), k[1]) for k in targetsR]
    for i, item in enumerate(targetsR):
        # new_outer_list_item = []
        if isinstance(item, str):
            pattern_string = item
            msg = ""
        # elif len(item) > 1 and isinstance(item[0], str): # Heuristic: pattern is a string, and there's a replacement
        else:
            pattern_string = item[0]
            msg = item[1]
        # try:
        #     new_outer_list_item = [re.compile(pattern_string), msg]
        # except re.error as e:
        #     print(f"Error compiling regex '{pattern_string}': {e}")
        targetsR[i] = [re.compile(pattern_string), msg]

    # print("\nCompiled targetsR:")
    # for item in targetsR:
    #     print(item)

    parse_dir()  # mod_path, mod_outpath
    # input("\nPRESS ANY KEY TO EXIT!")
        # Close the log file
    # if hasattr(log_file, 'close') and callable(getattr(log_file, 'close')) and not hasattr(log_file, 'closed') and not log_file.closed:
    #     log_file.close()
