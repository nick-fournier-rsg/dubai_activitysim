import pandas as pd
import numpy as np
import os


# Global
this_dir = os.path.dirname(__file__) # Relative
PopSim_dir = os.path.join('C:/Users/nick.fournier/Resource Systems Group, Inc',
                          'Model Development - Dubai RTA ABM Development Project',
                          'Task 3/PopulationSim')

# Employment, M = 'High end', L = 'Labourer', O = 'Non-construction'
col_dict = {'DP_POPULATION': 'TOTPOP',
            'DP_Total_Emp': 'TOTEMP',
            'DP_Work_M': 'MEMP',
            'DP_Work_L': 'LEMP',
            'DP_Work_O': 'OEMP',
            'DP_PRIMARYS': 'K_8',
            'DP_SECONDS': 'G9_12',
            'DP_UNIVERSITY': 'COLLEGE',
            'CarParkCostPerHour': 'OPRKCST',
            'AREATYPE': 'AREATYPE',
            }

taz_data = pd.read_csv(os.path.join(this_dir, 'inputs/model_TAZ.csv'))
dstm_mod = pd.read_csv(os.path.join(this_dir, 'inputs/DSTM_Mob_v01m08y2021_2020_StructureData.csv')).replace(' - ', 0)
persons = pd.read_csv(os.path.join(PopSim_dir, 'Output/emirati/synthetic_persons.csv'))
households = pd.read_csv(os.path.join(PopSim_dir, 'Output/emirati/synthetic_households.csv'))

# Set index
taz_data = taz_data.rename(columns={'Number': 'TAZ'}).set_index('TAZ')
dstm_mod = dstm_mod.rename(columns={'TAZ No.': 'TAZ'}).set_index('TAZ')
dstm_mod.columns = dstm_mod.columns.str.strip()

# Area type mapping from ZoneParkType
areatype_map = {'CBD': 1, 'OuterCBD': 2, 'NonCBD': 3, 'P+R': 4}
dstm_mod['AREATYPE'] = dstm_mod.ZoneParkType.str.strip().map(areatype_map)

# Get listof unique TAZ to ensure consistency later
taz_index = np.unique(np.concatenate([taz_data.index, dstm_mod.index, persons.TAZ.unique()]))


def create_landuse():
    # Geometric data
    print('Calculating geometric fields')
    lu_from_taz = pd.concat([
        # TAZ XY coords
        taz_data.TAZXCRD.to_frame('TAZXCRD'),
        taz_data.TAZYCRD.to_frame('TAZYCRD'),
        # Parking rates
        taz_data['Parking_rates_2020'].to_frame('PRKCST'),
        # Land area
        taz_data.AREA_HECT.to_frame('LANDAREA'),
        # Terminal time, default is 5 min?
        taz_data.INTERNALWALKTIME_PR.apply(lambda x: x if x>0 else 5).to_frame('TERMINAL'),
    ], axis=1)

    # Fill empty TAZs
    lu_from_taz = lu_from_taz.reindex(taz_index).fillna(-9)
    print('Aggregating person fields')
    lu_from_persons = pd.concat([
        # Number of persons
        #     persons.groupby(['TAZ']).size().to_frame('TOTPOP'),
        # Number of households
        persons.groupby('TAZ').household_id.nunique().to_frame('HH'),
        # Population in households
        persons.groupby('TAZ').size().to_frame('HHPOP'),
        # Population in group quarters (need to update GQ)
        persons.groupby('TAZ').size().to_frame('GQPOP') * 0,
    ], axis=1)

    # Fill empty TAZs
    lu_from_persons = lu_from_persons.reindex(taz_index).fillna(0)
    lu_from_model = dstm_mod[col_dict.keys()].rename(columns=col_dict)

    # Manually set fields
    print('Setting manually specified fields')
    lu_manual = pd.concat([
        # JURCODE ?
        pd.Series(data=0, index=taz_index).to_frame('JURCODE'),
        # TOPOLOGY - assume flat for now
        pd.Series(data=1, index=taz_index).to_frame('TOPOLOGY'),
    ], axis=1)

    # Combine and fillna
    print('Combine and save')
    land_use = pd.concat([
        lu_from_taz,
        lu_from_persons,
        lu_from_model,
        lu_manual,
    ], axis=1)

    land_use.index.name = 'TAZ'
    land_use.to_csv(os.path.join(this_dir, 'processing_data/processed/land_use.csv'), index=True)

    return land_use

if __name__ == "__main__":
    create_landuse()