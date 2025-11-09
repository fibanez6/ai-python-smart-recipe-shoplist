#!/usr/bin/env python3


import rich

from app.utils.json_extractor import JSONExtractor

rules_1 = {
    "sku": True,
    "sellingSize": True,
    "price.amount": True,

    # extract only first category name
    "categories": {
        "limit": 1,
        "fields": ["name"],
        "default": [],
    },

    # extract only first image URL
    "assets": {
        "limit": 1,
        "fields": ["url"],
    },

    # wildcard example - get all category names
    "categories[*].name": True,

    # regex filtering example for name field
    "name": {
        "regex": r"Tomato"
    },
}

json_data_1 = [
    {
        "sku": "000000000000457910",
        "name": "Cherry Tomatoes in Tomato Juice 400g",
        "sellingSize": "0.4 kg",
        "price": {"amount": 139},
        "categories": [{"name": "Pantry"}],
        "assets": [{"url": "https://dm.apac.cms..."}],
    },
    {
        "sku": "000000000000380347",
        "name": "Tomatoes 800g",
        "sellingSize": "0.8 kg",
        "price": {"amount": 299},
        "categories": [{"name": "Fruits & Vegetables"}],
        "assets": [{"url": "https://dm.apac.cms..."}],
    },
    {
        "sku": "000000000000380348",
        "name": "Bananas 1kg",
        "sellingSize": "1.0 kg",
        "price": {"amount": 450},
        "categories": [{"name": "Fruits & Vegetables"}],
        "assets": [{"url": "https://dm.apac.cms..."}],
    }
]


rules_2 = {
    "@": {
        "fields": ["name", "brandName", "quantityUnit", "sellingSize"],
    },
    "price": {
        "fields": ["amount", "amountRelevantDisplay", "comparisonDisplay"],
    },
    "categories[*].name": True,

    # extract only first image URL
    "assets": {
        "limit": 1,
        "fields": ["url"],
    },
}

json_data_2 = [
    {
        'sku': '000000000000457910',
        'name': 'Cherry Tomatoes in Tomato Juice 400g',
        'brandName': 'CASA BARELLI',
        'urlSlugText': 'casa-barelli-cherry-tomatoes-in-tomato-juice-400g',
        'discontinued': False,
        'notForSale': True,
        'quantityMin': 1,
        'quantityMax': 99,
        'quantityInterval': 1,
        'quantityDefault': 1,
        'quantityUnit': 'ea',
        'weightType': '0',
        'sellingSize': '0.4 kg',
        'price': {'amount': 139, 'amountRelevant': 139, 'amountRelevantDisplay': '$1.39', 'bottleDeposit': 0, 'bottleDepositDisplay': '$0.00', 'comparison': 348, 'comparisonDisplay': '$3.48 per 1 kg', 'currencyCode': 'AUD', 'currencySymbol': '$'},
        'categories': [
            {'id': '970000000', 'name': 'Pantry', 'urlSlugText': 'pantry'}, 
            {'id': '1111111171', 'name': 'Canned Food', 'urlSlugText': 'pantry/canned-food'}],
        'assets': [
            {'url': 'https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/0369db98-cf35-44d5-918c-3218f5934edb/{slug}', 'maxWidth': 1500, 'maxHeight': 1501, 'mimeType': 'image/*', 'assetType': 'FR01'},
            {'url': 'https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/9214239d-663d-4843-85a8-0f02da4dc135/{slug}', 'maxWidth': 1500, 'maxHeight': 1500, 'mimeType': 'image/*', 'assetType': 'FR02'},
            {'url': 'https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/0d7d6395-3f73-4729-8e08-9f69f978e4e4/{slug}', 'maxWidth': 1500, 'maxHeight': 1500, 'mimeType': 'image/*', 'assetType': 'FR03'},
            {'url': 'https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/a2a1b508-a265-4977-aa2a-61a0e5da814b/{slug}', 'maxWidth': 1500, 'maxHeight': 1500, 'mimeType': 'image/*', 'assetType': 'FR04'}
        ],
        'badges': []
    },
    {
        'sku': '000000000000380347',
        'name': 'Tomatoes 800g',
        'urlSlugText': 'no-brand-tomatoes-800g',
        'discontinued': False,
        'notForSale': True,
        'quantityMin': 1,
        'quantityMax': 99,
        'quantityInterval': 1,
        'quantityDefault': 1,
        'quantityUnit': 'ea',
        'weightType': '0',
        'sellingSize': '0.8 kg',
        'price': {'amount': 299, 'amountRelevant': 299, 'amountRelevantDisplay': '$2.99', 'bottleDeposit': 0, 'bottleDepositDisplay': '$0.00', 'comparison': 374, 'comparisonDisplay': '$3.74 per 1 kg', 'currencyCode': 'AUD', 'currencySymbol': '$'},
        'categories': [{'id': '950000000', 'name': 'Fruits & Vegetables', 'urlSlugText': 'fruits-vegetables'}, {'id': '1111111153', 'name': 'Fresh Vegetables', 'urlSlugText': 'fruits-vegetables/fresh-vegetables'}],
        'assets': [{'url': 'https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/a77d82a1-4987-49cc-8f25-f7bc4326da5f/{slug}', 'maxWidth': 1500, 'maxHeight': 1501, 'mimeType': 'image/*', 'assetType': 'FR01'}],
        'badges': []
    }
]

rules_3 = {
    "data": {
        "fields": [
            "name", 
            "brandName", 
            "quantityUnit", 
            "sellingSize"
        ],
        "price": ["amount", "amountRelevantDisplay", "comparisonDisplay"],
        "categories[*].name": True,
        "assets": {
            "limit": 1,
            "fields": ["url"],
        }
    },
}

json_data_3 = {
    "meta": {
        "spellingSuggestion": None,
        "pinned": [],
        "keywordRedirect": None,
        "pagination": {
            "offset": 0,
            "limit": 12,
            "totalCount": 54
        },
        "debug": None,
        "facets": [
            {
                "name": "category-tree",
                "localizedName": "Category",
                "docCount": 54,
                "activeValue": [],
                "config": {
                    "parameterName": "categoryTree",
                    "type": "value",
                    "isMultiValue": True,
                    "componentName": "category-tree",
                    "component": {
                        "name": "categoryTree",
                        "valueActive": None,
                        "valueInactive": None
                    }
                },
                "stats": None,
                "values": [
                    {
                        "key": "1588161425841179",
                        "docCount": 3,
                        "label": "Lower Prices",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "1588161420755352",
                        "docCount": 2,
                        "label": "Limited Time Only",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "950000000",
                        "docCount": 12,
                        "label": "Fruits & Vegetables",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111153",
                                "docCount": 12,
                                "label": "Fresh Vegetables",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "940000000",
                        "docCount": 3,
                        "label": "Meat & Seafood",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111146",
                                "docCount": 2,
                                "label": "Poultry",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111148",
                                "docCount": 1,
                                "label": "Seafood",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "930000000",
                        "docCount": 4,
                        "label": "Deli & Chilled Meats",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111138",
                                "docCount": 1,
                                "label": "Dips & Spreads",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111140",
                                "docCount": 3,
                                "label": "Antipasto",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "960000000",
                        "docCount": 1,
                        "label": "Dairy, Eggs & Fridge",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1588161408332097",
                                "docCount": 1,
                                "label": "Ready to Eat Meals",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "970000000",
                        "docCount": 31,
                        "label": "Pantry",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111171",
                                "docCount": 20,
                                "label": "Canned Food",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111173",
                                "docCount": 8,
                                "label": "Sauces",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111178",
                                "docCount": 2,
                                "label": "Condiments & Dressings",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111185",
                                "docCount": 1,
                                "label": "Lunch Box",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111188",
                                "docCount": 2,
                                "label": "Soups & Noodles",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "980000000",
                        "docCount": 2,
                        "label": "Freezer",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111197",
                                "docCount": 1,
                                "label": "Frozen Meat & Seafood",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            },
                            {
                                "key": "1111111198",
                                "docCount": 1,
                                "label": "Frozen Ready Meals",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "1000000000",
                        "docCount": 1,
                        "label": "Drinks",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": [
                            {
                                "key": "1111111208",
                                "docCount": 1,
                                "label": "Juices & Cordials",
                                "isSelected": False,
                                "thumbnail": None,
                                "children": []
                            }
                        ]
                    },
                    {
                        "key": "1588161427774115",
                        "docCount": 1,
                        "label": "Higher Protein Food and Drink",
                        "isSelected": False,
                        "thumbnail": None,
                        "children": []
                    }
                ]
            },
            {
                "name": "theme",
                "localizedName": "Theme",
                "docCount": 54,
                "activeValue": [],
                "config": {
                    "parameterName": "theme",
                    "type": "value",
                    "isMultiValue": True,
                    "componentName": "multi-select",
                    "component": {
                        "name": "multiSelect",
                        "valueActive": None,
                        "valueInactive": None
                    }
                },
                "stats": None,
                "values": [
                    {
                        "key": "Limited Time Only Meat",
                        "docCount": 2,
                        "label": "Limited Time Only Meat",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "Gardening",
                        "docCount": 1,
                        "label": "Gardening",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "Kitchen",
                        "docCount": 1,
                        "label": "Kitchen",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    }
                ]
            },
            {
                "name": "brand-name",
                "localizedName": "Brand Name",
                "docCount": 54,
                "activeValue": [],
                "config": {
                    "parameterName": "brandName",
                    "type": "value",
                    "isMultiValue": True,
                    "componentName": "multi-select",
                    "component": {
                        "name": "multiSelect",
                        "valueActive": None,
                        "valueInactive": None
                    }
                },
                "stats": None,
                "values": [
                    {
                        "key": "REMANO",
                        "docCount": 11,
                        "label": "REMANO",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "OCEAN RISE",
                        "docCount": 5,
                        "label": "OCEAN RISE",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "PORTVIEW",
                        "docCount": 4,
                        "label": "PORTVIEW",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "CORALE",
                        "docCount": 3,
                        "label": "CORALE",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "CASA BARELLI",
                        "docCount": 2,
                        "label": "CASA BARELLI",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "COLWAY",
                        "docCount": 2,
                        "label": "COLWAY",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "DELI ORIGINALS",
                        "docCount": 2,
                        "label": "DELI ORIGINALS",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "DELI ORIGINALS FRESH",
                        "docCount": 2,
                        "label": "DELI ORIGINALS FRESH",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "READY, SET…COOK!",
                        "docCount": 2,
                        "label": "READY, SET…COOK!",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "THE SOUP CO.",
                        "docCount": 2,
                        "label": "THE SOUP CO.",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "CROFTON",
                        "docCount": 1,
                        "label": "CROFTON",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "GARDENLINE",
                        "docCount": 1,
                        "label": "GARDENLINE",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "HEALTH & VITALITY",
                        "docCount": 1,
                        "label": "HEALTH & VITALITY",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "TASTE NATION",
                        "docCount": 1,
                        "label": "TASTE NATION",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "THE FISHMONGER",
                        "docCount": 1,
                        "label": "THE FISHMONGER",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "WESTCLIFF",
                        "docCount": 1,
                        "label": "WESTCLIFF",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    },
                    {
                        "key": "WORLD KITCHEN",
                        "docCount": 1,
                        "label": "WORLD KITCHEN",
                        "isSelected": None,
                        "thumbnail": None,
                        "children": []
                    }
                ]
            }
        ],
        "sort": [
            {
                "parameterName": "sort",
                "parameterValue": "relevance",
                "localizedName": "Relevance",
                "isActive": True
            },
            {
                "parameterName": "sort",
                "parameterValue": "name_asc",
                "localizedName": "Name (A to Z)",
                "isActive": False
            },
            {
                "parameterName": "sort",
                "parameterValue": "name_desc",
                "localizedName": "Name (Z to A)",
                "isActive": False
            },
            {
                "parameterName": "sort",
                "parameterValue": "price_asc",
                "localizedName": "Price (Low to High)",
                "isActive": False
            },
            {
                "parameterName": "sort",
                "parameterValue": "price_desc",
                "localizedName": "Price (High to Low)",
                "isActive": False
            }
        ]
    },
    "data": [
        {
            "sku": "000000000000457910",
            "name": "Cherry Tomatoes in Tomato Juice 400g",
            "brandName": "CASA BARELLI",
            "urlSlugText": "casa-barelli-cherry-tomatoes-in-tomato-juice-400g",
            "ageRestriction": None,
            "alcohol": None,
            "discontinued": False,
            "discontinuedNote": None,
            "notForSale": True,
            "notForSaleReason": None,
            "quantityMin": 1,
            "quantityMax": 99,
            "quantityInterval": 1,
            "quantityDefault": 1,
            "quantityUnit": "ea",
            "weightType": "0",
            "sellingSize": "0.4 kg",
            "energyClass": None,
            "onSaleDateDisplay": None,
            "price": {
                "amount": 139,
                "amountRelevant": 139,
                "amountRelevantDisplay": "$1.39",
                "bottleDeposit": 0,
                "bottleDepositDisplay": "$0.00",
                "comparison": 348,
                "comparisonDisplay": "$3.48 per 1 kg",
                "currencyCode": "AUD",
                "currencySymbol": "$",
                "perUnit": None,
                "perUnitDisplay": None,
                "wasPriceDisplay": None,
                "additionalInfo": None,
                "bottleDepositType": None,
                "feeText": None
            },
            "countryExtensions": None,
            "categories": [
                {
                    "id": "970000000",
                    "name": "Pantry",
                    "urlSlugText": "pantry"
                },
                {
                    "id": "1111111171",
                    "name": "Canned Food",
                    "urlSlugText": "pantry/canned-food"
                }
            ],
            "assets": [
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/0369db98-cf35-44d5-918c-3218f5934edb/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1501,
                    "mimeType": "image/*",
                    "assetType": "FR01",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/9214239d-663d-4843-85a8-0f02da4dc135/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "FR02",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/0d7d6395-3f73-4729-8e08-9f69f978e4e4/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "FR03",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/a2a1b508-a265-4977-aa2a-61a0e5da814b/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "FR04",
                    "alt": None,
                    "displayName": None
                }
            ],
            "badges": []
        },
        {
            "sku": "000000000000380347",
            "name": "Tomatoes 800g",
            "brandName": None,
            "urlSlugText": "no-brand-tomatoes-800g",
            "ageRestriction": None,
            "alcohol": None,
            "discontinued": False,
            "discontinuedNote": None,
            "notForSale": True,
            "notForSaleReason": None,
            "quantityMin": 1,
            "quantityMax": 99,
            "quantityInterval": 1,
            "quantityDefault": 1,
            "quantityUnit": "ea",
            "weightType": "0",
            "sellingSize": "0.8 kg",
            "energyClass": None,
            "onSaleDateDisplay": None,
            "price": {
                "amount": 299,
                "amountRelevant": 299,
                "amountRelevantDisplay": "$2.99",
                "bottleDeposit": 0,
                "bottleDepositDisplay": "$0.00",
                "comparison": 374,
                "comparisonDisplay": "$3.74 per 1 kg",
                "currencyCode": "AUD",
                "currencySymbol": "$",
                "perUnit": None,
                "perUnitDisplay": None,
                "wasPriceDisplay": None,
                "additionalInfo": None,
                "bottleDepositType": None,
                "feeText": None
            },
            "countryExtensions": None,
            "categories": [
                {
                    "id": "950000000",
                    "name": "Fruits & Vegetables",
                    "urlSlugText": "fruits-vegetables"
                },
                {
                    "id": "1111111153",
                    "name": "Fresh Vegetables",
                    "urlSlugText": "fruits-vegetables/fresh-vegetables"
                }
            ],
            "assets": [
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/a77d82a1-4987-49cc-8f25-f7bc4326da5f/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1501,
                    "mimeType": "image/*",
                    "assetType": "FR01",
                    "alt": None,
                    "displayName": None
                }
            ],
            "badges": []
        },
        {
            "sku": "000000000000370683",
            "name": "Tomato Sauce 2L",
            "brandName": "COLWAY",
            "urlSlugText": "colway-tomato-sauce-2l",
            "ageRestriction": None,
            "alcohol": None,
            "discontinued": False,
            "discontinuedNote": None,
            "notForSale": True,
            "notForSaleReason": None,
            "quantityMin": 1,
            "quantityMax": 99,
            "quantityInterval": 1,
            "quantityDefault": 1,
            "quantityUnit": "ea",
            "weightType": "0",
            "sellingSize": "2,000 ml",
            "energyClass": None,
            "onSaleDateDisplay": None,
            "price": {
                "amount": 499,
                "amountRelevant": 499,
                "amountRelevantDisplay": "$4.99",
                "bottleDeposit": 0,
                "bottleDepositDisplay": "$0.00",
                "comparison": 25,
                "comparisonDisplay": "$0.25 per 100 ml",
                "currencyCode": "AUD",
                "currencySymbol": "$",
                "perUnit": None,
                "perUnitDisplay": None,
                "wasPriceDisplay": None,
                "additionalInfo": None,
                "bottleDepositType": None,
                "feeText": None
            },
            "countryExtensions": None,
            "categories": [
                {
                    "id": "970000000",
                    "name": "Pantry",
                    "urlSlugText": "pantry"
                },
                {
                    "id": "1111111173",
                    "name": "Sauces",
                    "urlSlugText": "pantry/sauces"
                }
            ],
            "assets": [
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/6338c8e6-2d55-40ab-bca1-8efce3f3a6bf/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "FR01",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/c8c96b72-ae4c-4e8d-9277-267a32cc4b45/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "FR02",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/affd2553-81ad-422a-91a5-095a74e39b3a/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "NU01",
                    "alt": None,
                    "displayName": None
                },
                {
                    "url": "https://dm.apac.cms.aldi.cx/is/image/aldiprodapac/product/jpg/scaleWidth/{width}/8ea365ef-3e7c-46b2-8407-25fde2719770/{slug}",
                    "maxWidth": 1500,
                    "maxHeight": 1500,
                    "mimeType": "image/*",
                    "assetType": "IN01",
                    "alt": None,
                    "displayName": None
                }
            ],
            "badges": []
        }
    ]
}


def main():
    """Main function to test the API"""

    # Test with full price object
    rich.print("=== Test 1: Full price object ===")
    extractor = JSONExtractor(rules_1)
    result = extractor.extract(json_data_1)
    rich.print(result)

    # Test with full price object
    rich.print("=== Test 2: Full price object ===")
    extractor = JSONExtractor(rules_2)
    result = extractor.extract(json_data_2)
    rich.print(result)

    # Test with full price object
    rich.print("=== Test 3: Full price object ===")
    extractor = JSONExtractor(rules_3)
    result = extractor.extract(json_data_3)
    rich.print(result)


if __name__ == "__main__":
    main()