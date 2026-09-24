const STATS = {
 "medianWords": {
  "hl": 199.0,
  "hp": 85.5,
  "ll": 90.0,
  "lp": 91.5
 },
 "urls": {
  "hl": 6.02,
  "hp": 1.1,
  "ll": 0.94,
  "lp": 0.89
 },
 "urlAny": {
  "hl": 73.5,
  "hp": 47.8,
  "ll": 93.6,
  "lp": 88.7
 },
 "urgAny": {
  "hl": 7.5,
  "hp": 47.4,
  "ll": 27.5,
  "lp": 41.3
 },
 "ctaAny": {
  "hl": 16.5,
  "hp": 30.0,
  "ll": 16.6,
  "lp": 28.1
 },
 "caps": {
  "hl": 8.4,
  "hp": 9.0,
  "ll": 3.7,
  "lp": 3.3
 },
 "excl": {
  "hl": 2.23,
  "hp": 0.68,
  "ll": 0.37,
  "lp": 0.5
 },
 "urgency": {
  "verify": {
   "hl": 1.0,
   "hp": 15.4,
   "ll": 12.5,
   "lp": 20.8
  },
  "confirm": {
   "hl": 3.3,
   "hp": 17.6,
   "ll": 3.6,
   "lp": 5.4
  },
  "urgent": {
   "hl": 0.0,
   "hp": 1.8,
   "ll": 10.4,
   "lp": 8.7
  },
  "immediately": {
   "hl": 1.4,
   "hp": 7.0,
   "ll": 3.7,
   "lp": 6.8
  },
  "suspend": {
   "hl": 0.6,
   "hp": 4.8,
   "ll": 0.0,
   "lp": 0.6
  },
  "act now": {
   "hl": 0.3,
   "hp": 0.0,
   "ll": 0.6,
   "lp": 3.5
  },
  "expire": {
   "hl": 1.0,
   "hp": 10.6,
   "ll": 0.8,
   "lp": 2.1
  },
  "limited time": {
   "hl": 0.1,
   "hp": 0.2,
   "ll": 2.1,
   "lp": 3.9
  },
  "within 24 hours": {
   "hl": 0.0,
   "hp": 1.0,
   "ll": 0.0,
   "lp": 5.1
  },
  "final notice": {
   "hl": 0.0,
   "hp": 0.0,
   "ll": 0.0,
   "lp": 0.1
  },
  "locked": {
   "hl": 0.4,
   "hp": 1.2,
   "ll": 0.1,
   "lp": 0.1
  },
  "unauthorized": {
   "hl": 0.1,
   "hp": 1.4,
   "ll": 5.7,
   "lp": 9.6
  }
 },
 "words": {
  "hl": [
   [
    "mail",
    42
   ],
   [
    "wrote",
    37
   ],
   [
    "list",
    37
   ],
   [
    "use",
    31
   ],
   [
    "new",
    28
   ],
   [
    "listinfo",
    28
   ],
   [
    "message",
    27
   ],
   [
    "mailman",
    27
   ],
   [
    "like",
    27
   ],
   [
    "mailing",
    26
   ]
  ],
  "hp": [
   [
    "email",
    50
   ],
   [
    "account",
    46
   ],
   [
    "dear",
    33
   ],
   [
    "monkey",
    31
   ],
   [
    "mail",
    30
   ],
   [
    "click",
    27
   ],
   [
    "message",
    27
   ],
   [
    "information",
    26
   ],
   [
    "update",
    23
   ],
   [
    "new",
    22
   ]
  ],
  "ll": [
   [
    "dear",
    100
   ],
   [
    "regards",
    92
   ],
   [
    "finds",
    80
   ],
   [
    "link",
    77
   ],
   [
    "email",
    75
   ],
   [
    "hope",
    64
   ],
   [
    "thank",
    61
   ],
   [
    "click",
    56
   ],
   [
    "best",
    49
   ],
   [
    "warm",
    44
   ]
  ],
  "lp": [
   [
    "link",
    82
   ],
   [
    "dear",
    80
   ],
   [
    "regards",
    71
   ],
   [
    "click",
    62
   ],
   [
    "email",
    59
   ],
   [
    "finds",
    53
   ],
   [
    "hope",
    52
   ],
   [
    "thank",
    48
   ],
   [
    "best",
    43
   ],
   [
    "following",
    43
   ]
  ]
 },
 "counts": {
  "rows": {
   "hp": 1000,
   "hl": 1000,
   "lp": 1000,
   "ll": 1000
  },
  "distinct": {
   "lp": 1000,
   "ll": 998,
   "hl": 702,
   "hp": 500
  }
 },
 "accuracy": {
  "cv": {
   "overall": {
    "mean": 98.8,
    "sd": 0.6
   },
   "perGroup": {
    "hp": {
     "mean": 97.4,
     "sd": 1.5
    },
    "hl": {
     "mean": 99.1,
     "sd": 1.0
    },
    "lp": {
     "mean": 99.5,
     "sd": 0.4
    },
    "ll": {
     "mean": 98.4,
     "sd": 1.7
    }
   }
  },
  "heldOut": {
   "overall": 98.0,
   "perGroup": {
    "hp": 96.0,
    "hl": 97.9,
    "lp": 99.0,
    "ll": 98.0
   },
   "testSize": 640
  },
  "crossSource": {
   "human_to_llm": {
    "accuracy": 47.6,
    "balancedAccuracy": 47.6,
    "phishingRecall": 77.0,
    "legitRecall": 18.2,
    "predictedPhishing": 79.4
   },
   "llm_to_human": {
    "accuracy": 61.8,
    "balancedAccuracy": 57.4,
    "phishingRecall": 31.0,
    "legitRecall": 83.8,
    "predictedPhishing": 22.4
   }
  }
 },
 "topTerms": {
  "phishing": [
   [
    "link",
    4.098
   ],
   [
    "link com",
    3.704
   ],
   [
    "following link",
    3.511
   ],
   [
    "will",
    3.354
   ],
   [
    "monkey",
    3.202
   ],
   [
    "link https",
    3.099
   ],
   [
    "monkey org",
    3.088
   ],
   [
    "the following",
    2.882
   ],
   [
    "opportunity",
    2.875
   ],
   [
    "we have",
    2.756
   ],
   [
    "hello",
    2.734
   ],
   [
    "click on",
    2.709
   ],
   [
    "following",
    2.661
   ],
   [
    "we are",
    2.585
   ],
   [
    "2022",
    2.473
   ]
  ],
  "legit": [
   [
    "re",
    -4.193
   ],
   [
    "coordinator",
    -3.767
   ],
   [
    "here https",
    -3.328
   ],
   [
    "ms",
    -3.26
   ],
   [
    "dear mr",
    -3.249
   ],
   [
    "we re",
    -3.197
   ],
   [
    "dear ms",
    -3.153
   ],
   [
    "mr",
    -3.145
   ],
   [
    "sarah",
    -3.145
   ],
   [
    "click here",
    -2.765
   ],
   [
    "here",
    -2.697
   ],
   [
    "wrote",
    -2.689
   ],
   [
    "opensuse",
    -2.612
   ],
   [
    "http",
    -2.513
   ],
   [
    "company name",
    -2.422
   ]
  ]
 }
};
