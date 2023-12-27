states = {
    'AK': 'Alaska', 'AL': 'Alabama', 'AR': 'Arkansas',
    'AS': 'American Samoa', 'AZ': 'Arizona',
    'CA': 'California', 'CO': 'Colorado',
    'CT': 'Connecticut', 'DC': 'District of Columbia',
    'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'GU': 'Guam',
    'HI': 'Hawaii', 'IA': 'Iowa', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'MA': 'Massachusetts',
    'MD': 'Maryland', 'ME': 'Maine', 'MI': 'Michigan', 'MN': 'Minnesota',
    'MO': 'Missouri', 'MP': 'Northern Mariana Islands', 'MS': 'Mississippi',
    'MT': 'Montana', 'NC': 'North Carolina', 'ND': 'North Dakota',
    'NE': 'Nebraska', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NV': 'Nevada', 'NY': 'New York', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'PR': 'Puerto Rico', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
    'UT': 'Utah', 'VA': 'Virginia', 'VI': 'Virgin Islands',
    'VT': 'Vermont', 'WA': 'Washington', 'WI': 'Wisconsin',
    'WV': 'West Virginia', 'WY': 'Wyoming', 'AQ': 'American Samoa'
}

base_url = 'https://disclosures-clerk.house.gov'

table_end_text = "* For the complete list of asset"

trans_cols = [
    'Congressperson', 'District', 'Date', 'Notification Date',
    'Asset', 'Transaction Type', 'Amount', 'Cap Gains > $200?',
    'Filing Status', 'Description',
    'Subholding Of', 'Location', 'Comments', 'File'
]

table_cols = [
    "congressperson", "district", "date", "notification_date",
    "asset", "type", "amount", "cg200", "filing_status", "descrption",
    "subholding", "location", "comments", "file"
]

notes = [  # possible sub-heds for Asset text
        'Asset', 'Description', 'Filing Status', 'Subholding Of',
        'Location', 'Comments'
    ]

df_keys = [  # for output of PTR df
        'Filer',
        'Asset',
        'Description',
        'Filing Status',
        'Subholding Of',
        'Location',
        'Comments',
        'Transaction Type',
        'Date',
        'Notification Date',
        'Amount',
        'Min Amount',
        'Max Amount',
        'Cap Gains > $200?',
        'URL'
    ]

amount_key = {
    '$1,001 -': ("$1,001", "$15,000"),
    '$15,001 -': ("$15,001", "$50,000"),
    '$1,000,001 -': ("$1,000,001", "$5,000,000"),
    '$100,001 -': ("$100,001", "$250,000"),
    '$250,001 -': ("$250,001", "$500,000"),
    '$500,001 -': ("$500,001", "$1,000,000"),
    '$50,001 -': ("$50,001", "$100,000"),
    '$5,000,001 -': ("$5,000,001", "$25,000,000")
}