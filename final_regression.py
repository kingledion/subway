#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 20 08:31:35 2018

@author: dhartig
"""

from regression import loadData, citylist, scoreCV, linearF, logF, poissonF, poissIdentF, LADF
import itertools, numpy as np



def printScores():
    
    cycle = [(linFeat, 'Linear', linearF),
             (logFeat, 'Log', logF),
             (poissFeat, 'Poisson', poissonF),
             (poissIFeat, 'PoissIdent', poissIdentF),
             #(LADFeat, 'LAD', LADF),
             (linFeatL, 'LinearLASSO', linearF),
             (logFeatL, 'LogLASSO', logF),
             (poissFeatL, 'PoissonLASSO', poissonF),
             (poissIFeatL, 'PoissIdentLASSO', poissIdentF),
             #(LADFeatL, 'LAD LASSO', LADF),
             (basefeat, 'Pop + Emp', linearF),
             (singlefeat, 'Single', linearF),
             (rf5Feat, 'RF 5', linearF),
             (rf10Feat, 'RF 10', linearF)]
    
    pairs = []
    combs = list(itertools.combinations(citylist, r=5))
    for l1, l2 in zip(combs, [set(citylist) - set(c) for c in combs]):
        df1 = loadData(l1, droptransfer=True)
        df2 = loadData(l2, droptransfer=True)
        pairs.append((df1, df2))
    
    
    for feats, name, func in cycle:
        scores = scoreCV(func, pairs, feats, None)
        
        print(name)
        print(np.min([x[0] for x in scores]), np.min([x[1] for x in scores])) 
        print(len(feats))
        print(np.mean([x[0] for x in scores]), np.mean([x[1] for x in scores]))
        print()
        
linFeat = ['15net_hunits_old',
        '15net_university',
        'near_hunits_large',
        '30net_hunits_large',
        '30net_emp_pay',
        'near_hunits_detached',
        'near_hospitality',
        'near_entertainment',
        'near_hunits_new',
        '15net_pop_child',
        'near_foreign_born',
        'near_pop_poor'
        ]


linFeatL = ['15net_hospitality', 
        '15net_hunits_attached',
        '15net_hunits_medium',
        'near_emp_pay',
        'near_hospitality',
        '30net_medical',
        'near_pop_old',
        'near_university',
        'parking'
        ]

logFeat = ['30net_entertainment',
        'near_house_w_child',
        'near_family',
        'near_population',
        'near_pop_child',
        'near_employment',
        'near_hunits_large',
        'near_hospitality',
        '15net_entertainment',
        '30net_university',
        'near_emp_pay',
        '15net_university',
        'near_finance',
        'near_entertainment',
        'parking',
        'near_hunits_old',
        ]

logFeatL = ['near_entertainment',
        'near_hospitality',
        'parking',
        '15net_hunits_vacant',
        '30net_hospitality',
        '30net_hunits_detached',
        '30net_hunits_large',
        'near_employment',
        'near_labor_force',
        'near_university',
        '15net_hunits_attached',
        '15net_hunits_old',
        '15net_university',
        '30net_hunits_medium',
        '30net_medical',
        'near_hunits_attached',
        'near_hunits_new',
        'near_hunits_owner',
        'near_medical'
        ]

poissFeat = ['15net_hunits_old',
        '30net_medical',
        'near_pop_old',
        '30net_hunits_large',
        '30net_entertainment',
        '15net_medical',
        'near_university',
        'near_hunits_detached',
        'near_population',
        'near_medical',
        '15net_university',
        'parking',
        'near_hospitality',
        'near_family',
        'near_business'
        ]

poissFeatL = ['near_hospitality',
        '15net_hunits_attached',
        'near_university',
        'parking',
        '15net_hunits_medium',
        '15net_hunits_vacant',
        '30net_hospitality',
        'near_employment',
        'near_entertainment',
        'near_pop_old'
        ]

poissIFeat = ['15net_hunits_old',
        'near_hospitality',
        '30net_medical',
        'near_pop_old',
        '30net_hunits_old',
        'parking',
        'near_university',
        'near_medical'
        ]

poissIFeatL = ['15net_hunits_medium',
        'near_hospitality',
        'parking',
        '15net_hospitality',
        'near_emp_pay',
        'near_university',
        '15net_hunits_attached',
        '30net_medical',
        'near_hunits_attached',
        'near_pop_old'
        ]

LADFeat = ['15net_employed',
        'near_hospitality',
        'near_hunits_owner',
        '30net_population'
        ]

LADFeatL = ['near_business',
        'near_emp_pay',
        'near_entertainment',
        'near_hunits_owner',
        'parking',
        '15net_bachelors',
        '15net_employed',
        '15net_hospitality',
        '15net_hunits_attached',
        '30net_hunits_large',
        '15net_hunits_old',
        'near_employment',
        'near_hospitality',
        'near_hunits_attached',
        'near_labor_force',
        'near_pop_rich',
        '15net_household',
        '15net_emp_pay',
        '15net_medical',
        '30net_medical',
        '30net_hunits_vacant',
        '15net_hunits_medium',
        '30net_hunits_medium'
        ]

rf5Feat = ['near_emp_pay', 'near_employment', '15net_hospitality', '15net_hunits_medium', 'near_hospitality']

rf10Feat = ['near_emp_pay', 'near_employment', '15net_hospitality', '15net_hunits_medium', 'near_hospitality',
            '15net_bachelors', '15net_emp_pay', '15net_pop_rich', '15net_employment', '15net_hunits_old']

basefeat = ['near_population', 'near_employment']
singlefeat = ['15net_hunits_old']

if __name__ == "__main__":
    printScores()