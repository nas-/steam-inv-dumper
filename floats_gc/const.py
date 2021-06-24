fades = {
    'Bowie Knife': [80, 1],
    'Huntsman Knife': [80, 1],
    'M9 Bayonet': [80, 1],
    'Bayonet': [80, 1],
    'Flip Knife': [80, 1],
    'Gut Knife': [80, 1],
    'Shadow Daggers': [80, 1],
    'Karambit': [80, -1],
    'Butterfly Knife': [80, 1],
    'Falchion Knife': [80, 1]
}

order = [146, 602, 393, 994, 359, 541, 688, 129, 792, 412, 281, 743, 787, 241, 182, 332, 16, 628, 152, 701, 673, 292,
         204, 344, 649, 923, 908, 705, 777, 918, 780, 356, 126, 652, 252, 832, 988, 457, 685, 660, 112, 522, 773, 736,
         982, 578, 873, 340, 230, 48, 274, 607, 795, 471, 867, 452, 621, 653, 874, 761, 826, 683, 14, 770, 949, 454,
         803, 1000, 243, 108, 876, 32, 58, 444, 614, 213, 728, 631, 405, 696, 8, 461, 233, 854, 202, 337, 702, 5, 971,
         378, 539, 178, 966, 171, 672, 732, 188, 370, 493, 406, 922, 287, 149, 655, 165, 997, 817, 516, 959, 591, 121,
         589, 637, 546, 238, 656, 545, 706, 766, 977, 559, 844, 68, 402, 351, 499, 206, 632, 329, 976, 868, 28, 809,
         791, 372, 195, 156, 972, 177, 785, 397, 90, 459, 725, 203, 553, 962, 483, 441, 232, 756, 941, 753, 473, 764,
         727, 710, 626, 858, 537, 561, 818, 909, 590, 254, 404, 805, 125, 810, 930, 674, 110, 27, 309, 485, 691, 869,
         315, 647, 980, 448, 183, 400, 196, 9, 496, 948, 321, 307, 216, 989, 60, 535, 328, 463, 746, 663, 364, 234, 333,
         71, 506, 222, 266, 411, 170, 582, 794, 717, 413, 445, 958, 62, 415, 353, 845, 605, 670, 931, 846, 667, 812,
         438, 630, 570, 138, 334, 3, 822, 723, 907, 354, 296, 304, 0, 1, 98, 489, 555, 624, 148, 385, 569, 335, 894,
         253, 368, 515, 593, 606, 611, 899, 311, 102, 451, 547, 388, 54, 142, 767, 436, 42, 280, 939, 269, 642, 598,
         783, 507, 262, 853, 4, 693, 45, 733, 384, 579, 532, 552, 479, 258, 709, 96, 185, 387, 678, 929, 143, 540, 425,
         164, 217, 310, 162, 189, 151, 20, 820, 716, 530, 246, 776, 160, 689, 580, 843, 680, 66, 480, 325, 49, 218, 184,
         220, 450, 373, 560, 88, 616, 610, 113, 730, 250, 574, 998, 174, 284, 394, 303, 744, 193, 369, 24, 504, 627,
         464, 992, 286, 551, 119, 443, 969, 477, 529, 226, 498, 116, 492, 865, 715, 531, 419, 409, 106, 699, 235, 750,
         919, 999, 7, 166, 594, 31, 935, 374, 951, 816, 857, 190, 861, 432, 954, 526, 852, 13, 290, 646, 893, 859, 360,
         265, 720, 684, 408, 659, 928, 194, 383, 209, 694, 973, 72, 59, 839, 423, 638, 913, 153, 883, 39, 259, 600, 410,
         134, 44, 237, 371, 352, 896, 595, 77, 434, 349, 490, 469, 603, 317, 279, 772, 355, 731, 75, 510, 983, 83, 248,
         115, 221, 544, 926, 650, 871, 244, 502, 484, 986, 711, 927, 231, 634, 721, 855, 306, 558, 952, 523, 386, 675,
         478, 132, 784, 186, 788, 398, 476, 534, 890, 339, 862, 263, 542, 679, 497, 708, 739, 197, 557, 219, 519, 562,
         472, 198, 127, 796, 159, 669, 467, 169, 407, 208, 585, 242, 330, 417, 362, 456, 17, 135, 681, 131, 748, 320,
         268, 275, 692, 338, 101, 122, 180, 420, 987, 158, 671, 509, 261, 779, 503, 474, 704, 505, 144, 609, 15, 622,
         225, 100, 682, 288, 495, 623, 366, 247, 937, 120, 92, 581, 833, 426, 500, 305, 99, 316, 768, 35, 985, 965, 755,
         81, 945, 771, 391, 563, 319, 882, 418, 934, 618, 331, 239, 36, 215, 786, 565, 724, 643, 74, 501, 906, 264, 123,
         957, 713, 70, 938, 199, 192, 56, 267, 128, 26, 543, 40, 775, 257, 524, 270, 615, 322, 86, 620, 879, 880, 245,
         842, 124, 932, 367, 707, 350, 888, 836, 635, 460, 52, 662, 55, 363, 25, 200, 346, 900, 831, 870, 847, 722, 625,
         814, 718, 347, 830, 850, 970, 69, 700, 51, 365, 799, 82, 214, 548, 619, 905, 85, 327, 644, 819, 889, 877, 963,
         613, 91, 297, 567, 19, 533, 207, 629, 133, 778, 765, 797, 823, 741, 38, 837, 390, 97, 841, 964, 950, 10, 255,
         300, 641, 439, 676, 729, 50, 735, 175, 67, 617, 379, 139, 967, 65, 554, 734, 357, 140, 228, 695, 738, 903, 61,
         271, 95, 272, 947, 996, 427, 829, 904, 661, 828, 294, 53, 475, 573, 978, 343, 318, 2, 301, 491, 453, 470, 437,
         251, 518, 414, 512, 291, 584, 118, 298, 654, 167, 801, 114, 592, 912, 78, 556, 604, 240, 804, 946, 920, 323,
         588, 991, 431, 924, 885, 342, 864, 901, 806, 737, 884, 666, 163, 633, 63, 760, 902, 549, 942, 273, 312, 382,
         697, 57, 802, 916, 974, 866, 187, 835, 111, 18, 23, 596, 277, 851, 984, 886, 933, 645, 995, 990, 921, 179, 421,
         774, 117, 528, 416, 821, 808, 289, 376, 389, 769, 79, 176, 758, 299, 955, 104, 895, 740, 658, 993, 757, 157,
         442, 815, 446, 979, 433, 752, 863, 22, 276, 487, 324, 587, 811, 47, 698, 154, 860, 392, 361, 37, 878, 285, 336,
         875, 191, 293, 161, 538, 898, 953, 782, 719, 227, 612, 424, 429, 212, 513, 586, 762, 687, 109, 210, 155, 33,
         481, 960, 76, 302, 790, 887, 915, 564, 6, 749, 103, 94, 168, 568, 12, 458, 440, 466, 525, 73, 798, 295, 677,
         89, 686, 508, 381, 430, 30, 377, 145, 260, 536, 891, 511, 566, 940, 282, 759, 488, 283, 130, 21, 223, 514, 813,
         665, 181, 211, 608, 64, 43, 314, 249, 917, 597, 640, 447, 173, 172, 572, 726, 712, 80, 881, 657, 229, 435, 455,
         308, 236, 401, 482, 358, 838, 703, 313, 136, 462, 11, 849, 395, 465, 46, 690, 278, 137, 956, 840, 224, 29, 141,
         781, 827, 599, 751, 789, 375, 872, 486, 150, 345, 793, 449, 84, 399, 824, 754, 639, 856, 936, 396, 968, 550,
         494, 914, 201, 571, 747, 517, 147, 577, 800, 943, 981, 107, 745, 34, 668, 664, 105, 428, 834, 925, 422, 975,
         714, 944, 648, 848, 380, 576, 825, 256, 521, 807, 326, 911, 205, 583, 41, 601, 897, 87, 527, 651, 742, 892,
         468, 348, 341, 910, 636, 403, 520, 961, 93, 575, 763]

doppler = {
    '415': 'Ruby',
    '416': 'Sapphire',
    '417': 'Black Pearl',
    '617': 'Black Pearl',
    '418': 'Phase 1',
    '419': 'Phase 2',
    '420': 'Phase 3',
    '421': 'Phase 4',
    '568': 'Emerald',
    '569': 'Phase 1',
    '570': 'Phase 2',
    '571': 'Phase 3',
    '572': 'Phase 4',
    '619': 'Sapphire',
    '618': 'Phase 2',
    '852': 'Phase 1',
    '854':'Phase 3',
    '853':'Phase 2',
    '855':'Phase 4'

}

marbles = {
    "Karambit": {
        "3": "FFI",
        "5": "8th Max",
        "8": "7th Max",
        "9": "FFI",
        "14": "7th Max",
        "16": "2nd Max",
        "27": "FFI",
        "28": "10th Max",
        "32": "7th Max",
        "48": "4th Max",
        "58": "7th Max",
        "60": "FFI",
        "62": "FFI",
        "68": "9th Max",
        "71": "FFI",
        "90": "FFI",
        "108": "7th Max",
        "110": "FFI",
        "112": "6th Max",
        "121": "9th Max",
        "125": "FFI",
        "126": "4th Max",
        "129": "4th Max",
        "146": "2nd Max",
        "149": "9th Max",
        "152": "3rd Max",
        "156": "10th Max",
        "165": "9th Max",
        "170": "FFI",
        "171": "9th Max",
        "177": "10th Max",
        "178": "8th Max",
        "182": "5th Max",
        "183": "FFI",
        "188": "8th Max",
        "195": "FFI",
        "196": "FFI",
        "202": "8th Max",
        "203": "FFI",
        "204": "5th Max",
        "206": "9th Max",
        "213": "7th Max",
        "216": "FFI",
        "222": "FFI",
        "230": "6th Max",
        "232": "FFI",
        "233": "7th Max",
        "234": "FFI",
        "238": "10th Max",
        "241": "2nd Max",
        "243": "7th Max",
        "252": "5th Max",
        "254": "FFI",
        "266": "FFI",
        "274": "7th Max",
        "281": "3rd Max",
        "287": "9th Max",
        "292": "3rd Max",
        "307": "FFI",
        "309": "FFI",
        "315": "FFI",
        "321": "FFI",
        "328": "FFI",
        "329": "FFI",
        "332": "4th Max",
        "333": "FFI",
        "337": "8th Max",
        "340": "6th Max",
        "344": "3rd Max",
        "351": "FFI",
        "356": "6th Max",
        "359": "2nd Max",
        "364": "FFI",
        "370": "9th Max",
        "372": "FFI",
        "378": "8th Max",
        "393": "2nd Max",
        "397": "FFI",
        "400": "FFI",
        "402": "10th Max",
        "404": "FFI",
        "405": "7th Max",
        "406": "8th Max",
        "411": "FFI",
        "412": "1st Max",
        "413": "FFI",
        "438": "FFI",
        "441": "FFI",
        "444": "6th Max",
        "445": "FFI",
        "448": "FFI",
        "452": "6th Max",
        "454": "7th Max",
        "457": "5th Max",
        "459": "FFI",
        "461": "8th Max",
        "463": "FFI",
        "471": "6th Max",
        "473": "FFI",
        "483": "FFI",
        "485": "FFI",
        "493": "9th Max",
        "496": "FFI",
        "499": "9th Max",
        "506": "FFI",
        "516": "9th Max",
        "522": "5th Max",
        "535": "FFI",
        "537": "FFI",
        "539": "8th Max",
        "541": "2nd Max",
        "545": "10th Max",
        "546": "10th Max",
        "553": "10th Max",
        "559": "10th Max",
        "561": "FFI",
        "578": "5th Max",
        "582": "FFI",
        "589": "10th Max",
        "590": "FFI",
        "591": "10th Max",
        "602": "2nd Max",
        "605": "FFI",
        "607": "6th Max",
        "614": "7th Max",
        "621": "6th Max",
        "624": "FFI",
        "626": "FFI",
        "628": "3rd Max",
        "630": "FFI",
        "631": "6th Max",
        "632": "FFI",
        "637": "9th Max",
        "647": "FFI",
        "649": "2nd Max",
        "652": "5th Max",
        "653": "7th Max",
        "655": "8th Max",
        "656": "9th Max",
        "660": "5th Max",
        "663": "FFI",
        "667": "FFI",
        "670": "FFI",
        "672": "9th Max",
        "673": "3rd Max",
        "674": "FFI",
        "683": "7th Max",
        "685": "5th Max",
        "688": "2nd Max",
        "691": "FFI",
        "696": "8th Max",
        "701": "2nd Max",
        "702": "7th Max",
        "705": "5th Max",
        "706": "9th Max",
        "710": "FFI",
        "717": "FFI",
        "723": "FFI",
        "725": "10th Max",
        "727": "FFI",
        "728": "7th Max",
        "732": "7th Max",
        "736": "5th Max",
        "743": "3rd Max",
        "746": "FFI",
        "753": "FFI",
        "756": "FFI",
        "761": "6th Max",
        "764": "10th Max",
        "766": "9th Max",
        "770": "7th Max",
        "773": "6th Max",
        "777": "3rd Max",
        "780": "4th Max",
        "785": "FFI",
        "787": "4th Max",
        "791": "10th Max",
        "792": "3rd Max",
        "794": "FFI",
        "795": "7th Max",
        "803": "7th Max",
        "805": "FFI",
        "809": "FFI",
        "810": "10th Max",
        "817": "9th Max",
        "818": "FFI",
        "822": "FFI",
        "826": "7th Max",
        "832": "5th Max",
        "844": "10th Max",
        "845": "FFI",
        "846": "FFI",
        "854": "8th Max",
        "858": "10th Max",
        "867": "7th Max",
        "868": "10th Max",
        "869": "FFI",
        "873": "6th Max",
        "874": "4th Max",
        "876": "6th Max",
        "908": "4th Max",
        "909": "FFI",
        "918": "4th Max",
        "922": "9th Max",
        "923": "4th Max",
        "930": "FFI",
        "931": "FFI",
        "941": "FFI",
        "948": "FFI",
        "949": "7th Max",
        "958": "FFI",
        "959": "9th Max",
        "962": "FFI",
        "966": "8th Max",
        "971": "8th Max",
        "972": "10th Max",
        "976": "FFI",
        "977": "10th Max",
        "980": "FFI",
        "982": "6th Max",
        "988": "5th Max",
        "989": "FFI",
        "994": "3rd Max",
        "997": "9th Max",
    },
    "Bayonet": {
        "5": "FFI",
        "8": "7th Max",
        "9": "FFI",
        "14": "7th Max",
        "16": "2nd Max",
        "27": "FFI",
        "28": "FFI",
        "32": "7th Max",
        "48": "4th Max",
        "58": "7th Max",
        "68": "FFI",
        "71": "FFI",
        "90": "FFI",
        "108": "7th Max",
        "110": "FFI",
        "112": "6th Max",
        "121": "FFI",
        "125": "FFI",
        "126": "4th Max",
        "129": "4th Max",
        "146": "2nd Max",
        "149": "FFI",
        "152": "3rd Max",
        "156": "FFI",
        "165": "FFI",
        "171": "FFI",
        "177": "FFI",
        "178": "FFI",
        "182": "5th Max",
        "183": "FFI",
        "188": "FFI",
        "195": "FFI",
        "196": "FFI",
        "202": "FFI",
        "203": "FFI",
        "204": "5th Max",
        "206": "FFI",
        "213": "7th Max",
        "230": "6th Max",
        "232": "FFI",
        "233": "7th Max",
        "238": "FFI",
        "241": "2nd Max",
        "243": "7th Max",
        "252": "5th Max",
        "254": "FFI",
        "274": "7th Max",
        "281": "3rd Max",
        "287": "FFI",
        "292": "3rd Max",
        "309": "FFI",
        "329": "FFI",
        "332": "4th Max",
        "337": "FFI",
        "340": "6th Max",
        "344": "3rd Max",
        "351": "FFI",
        "356": "6th Max",
        "359": "2nd Max",
        "370": "FFI",
        "372": "FFI",
        "378": "FFI",
        "393": "2nd Max",
        "397": "FFI",
        "402": "FFI",
        "404": "FFI",
        "405": "7th Max",
        "406": "FFI",
        "412": "1st Max",
        "441": "FFI",
        "444": "6th Max",
        "448": "FFI",
        "452": "6th Max",
        "454": "7th Max",
        "457": "5th Max",
        "459": "FFI",
        "461": "FFI",
        "471": "6th Max",
        "473": "FFI",
        "483": "FFI",
        "493": "FFI",
        "499": "FFI",
        "506": "FFI",
        "516": "FFI",
        "522": "5th Max",
        "537": "FFI",
        "539": "FFI",
        "541": "2nd Max",
        "545": "FFI",
        "546": "FFI",
        "553": "FFI",
        "559": "FFI",
        "561": "FFI",
        "578": "5th Max",
        "589": "FFI",
        "590": "FFI",
        "591": "FFI",
        "602": "2nd Max",
        "607": "6th Max",
        "614": "7th Max",
        "621": "6th Max",
        "626": "FFI",
        "628": "3rd Max",
        "631": "6th Max",
        "632": "FFI",
        "637": "FFI",
        "647": "FFI",
        "649": "2nd Max",
        "652": "5th Max",
        "653": "7th Max",
        "655": "FFI",
        "656": "FFI",
        "660": "5th Max",
        "672": "FFI",
        "673": "3rd Max",
        "674": "FFI",
        "683": "7th Max",
        "685": "5th Max",
        "688": "2nd Max",
        "696": "FFI",
        "701": "2nd Max",
        "702": "7th Max",
        "705": "5th Max",
        "706": "FFI",
        "710": "FFI",
        "725": "FFI",
        "727": "FFI",
        "728": "7th Max",
        "732": "7th Max",
        "736": "5th Max",
        "743": "3rd Max",
        "753": "FFI",
        "756": "FFI",
        "761": "6th Max",
        "764": "FFI",
        "766": "FFI",
        "770": "7th Max",
        "773": "6th Max",
        "777": "3rd Max",
        "780": "4th Max",
        "785": "FFI",
        "787": "4th Max",
        "791": "FFI",
        "792": "3rd Max",
        "795": "7th Max",
        "803": "7th Max",
        "805": "FFI",
        "809": "FFI",
        "810": "FFI",
        "817": "FFI",
        "818": "FFI",
        "826": "7th Max",
        "832": "5th Max",
        "844": "FFI",
        "854": "FFI",
        "858": "FFI",
        "867": "7th Max",
        "868": "FFI",
        "869": "FFI",
        "873": "6th Max",
        "874": "4th Max",
        "876": "6th Max",
        "908": "4th Max",
        "909": "FFI",
        "918": "4th Max",
        "922": "FFI",
        "923": "4th Max",
        "930": "FFI",
        "941": "FFI",
        "949": "7th Max",
        "959": "FFI",
        "962": "FFI",
        "966": "FFI",
        "971": "FFI",
        "972": "FFI",
        "976": "FFI",
        "977": "FFI",
        "980": "FFI",
        "982": "6th Max",
        "988": "5th Max",
        "989": "FFI",
        "994": "3rd Max",
        "997": "FFI",
    },
    "Flip Knife": {
        "5": "FFI",
        "8": "FFI",
        "9": "FFI",
        "14": "FFI",
        "16": "2nd Max",
        "27": "FFI",
        "28": "FFI",
        "32": "FFI",
        "48": "FFI",
        "58": "FFI",
        "68": "FFI",
        "71": "FFI",
        "90": "FFI",
        "108": "FFI",
        "110": "FFI",
        "112": "FFI",
        "121": "FFI",
        "125": "FFI",
        "126": "4th Max",
        "129": "4th Max",
        "146": "2nd Max",
        "149": "FFI",
        "152": "3rd Max",
        "156": "FFI",
        "165": "FFI",
        "171": "FFI",
        "177": "FFI",
        "178": "FFI",
        "182": "FFI",
        "183": "FFI",
        "188": "FFI",
        "195": "FFI",
        "196": "FFI",
        "202": "FFI",
        "203": "FFI",
        "204": "FFI",
        "206": "FFI",
        "213": "FFI",
        "230": "FFI",
        "232": "FFI",
        "233": "FFI",
        "238": "FFI",
        "241": "2nd Max",
        "243": "FFI",
        "252": "FFI",
        "254": "FFI",
        "274": "FFI",
        "281": "3rd Max",
        "287": "FFI",
        "292": "3rd Max",
        "309": "FFI",
        "329": "FFI",
        "332": "4th Max",
        "337": "FFI",
        "340": "FFI",
        "344": "3rd Max",
        "351": "FFI",
        "356": "FFI",
        "359": "2nd Max",
        "370": "FFI",
        "372": "FFI",
        "378": "FFI",
        "393": "2nd Max",
        "397": "FFI",
        "402": "FFI",
        "404": "FFI",
        "405": "FFI",
        "406": "FFI",
        "412": "1st Max",
        "441": "FFI",
        "444": "FFI",
        "448": "FFI",
        "452": "FFI",
        "454": "FFI",
        "457": "FFI",
        "459": "FFI",
        "461": "FFI",
        "471": "FFI",
        "473": "FFI",
        "483": "FFI",
        "493": "FFI",
        "499": "FFI",
        "506": "FFI",
        "516": "FFI",
        "522": "FFI",
        "537": "FFI",
        "539": "FFI",
        "541": "2nd Max",
        "545": "FFI",
        "546": "FFI",
        "553": "FFI",
        "559": "FFI",
        "561": "FFI",
        "578": "FFI",
        "589": "FFI",
        "590": "FFI",
        "591": "FFI",
        "602": "2nd Max",
        "607": "FFI",
        "614": "FFI",
        "621": "FFI",
        "626": "FFI",
        "628": "3rd Max",
        "631": "FFI",
        "632": "FFI",
        "637": "FFI",
        "647": "FFI",
        "649": "2nd Max",
        "652": "FFI",
        "653": "FFI",
        "655": "FFI",
        "656": "FFI",
        "660": "FFI",
        "672": "FFI",
        "673": "3rd Max",
        "674": "FFI",
        "683": "FFI",
        "685": "FFI",
        "688": "2nd Max",
        "696": "FFI",
        "701": "2nd Max",
        "702": "FFI",
        "705": "FFI",
        "706": "FFI",
        "710": "FFI",
        "725": "FFI",
        "727": "FFI",
        "728": "FFI",
        "732": "FFI",
        "736": "FFI",
        "743": "3rd Max",
        "753": "FFI",
        "756": "FFI",
        "761": "FFI",
        "764": "FFI",
        "766": "FFI",
        "770": "FFI",
        "773": "FFI",
        "777": "3rd Max",
        "780": "FFI",
        "785": "FFI",
        "787": "4th Max",
        "791": "FFI",
        "792": "3rd Max",
        "795": "FFI",
        "803": "FFI",
        "805": "FFI",
        "809": "FFI",
        "810": "FFI",
        "817": "FFI",
        "818": "FFI",
        "826": "FFI",
        "832": "FFI",
        "844": "FFI",
        "854": "FFI",
        "858": "FFI",
        "867": "FFI",
        "868": "FFI",
        "869": "FFI",
        "873": "FFI",
        "874": "4th Max",
        "876": "FFI",
        "908": "4th Max",
        "909": "FFI",
        "918": "4th Max",
        "922": "FFI",
        "923": "4th Max",
        "930": "FFI",
        "941": "FFI",
        "949": "FFI",
        "959": "FFI",
        "962": "FFI",
        "966": "FFI",
        "971": "FFI",
        "972": "FFI",
        "976": "FFI",
        "977": "FFI",
        "980": "FFI",
        "982": "FFI",
        "988": "FFI",
        "989": "FFI",
        "994": "3rd Max",
        "997": "FFI",
    },
    "Gut Knife": {
        "5": "FFI",
        "8": "7th Max",
        "9": "FFI",
        "14": "7th Max",
        "16": "2nd Max",
        "27": "FFI",
        "28": "FFI",
        "32": "7th Max",
        "48": "4th Max",
        "58": "7th Max",
        "68": "FFI",
        "71": "FFI",
        "90": "FFI",
        "108": "7th Max",
        "110": "FFI",
        "112": "6th Max",
        "121": "FFI",
        "125": "FFI",
        "126": "4th Max",
        "129": "4th Max",
        "146": "2nd Max",
        "149": "FFI",
        "152": "3rd Max",
        "156": "FFI",
        "165": "FFI",
        "171": "FFI",
        "177": "FFI",
        "178": "FFI",
        "182": "5th Max",
        "183": "FFI",
        "188": "FFI",
        "195": "FFI",
        "196": "FFI",
        "202": "FFI",
        "203": "FFI",
        "204": "5th Max",
        "206": "FFI",
        "213": "7th Max",
        "230": "6th Max",
        "232": "FFI",
        "233": "7th Max",
        "238": "FFI",
        "241": "2nd Max",
        "243": "7th Max",
        "252": "5th Max",
        "254": "FFI",
        "274": "7th Max",
        "281": "3rd Max",
        "287": "FFI",
        "292": "3rd Max",
        "309": "FFI",
        "329": "FFI",
        "332": "4th Max",
        "337": "FFI",
        "340": "6th Max",
        "344": "3rd Max",
        "351": "FFI",
        "356": "6th Max",
        "359": "2nd Max",
        "370": "FFI",
        "372": "FFI",
        "378": "FFI",
        "393": "2nd Max",
        "397": "FFI",
        "402": "FFI",
        "404": "FFI",
        "405": "7th Max",
        "406": "FFI",
        "412": "1st Max",
        "441": "FFI",
        "444": "6th Max",
        "448": "FFI",
        "452": "6th Max",
        "454": "7th Max",
        "457": "5th Max",
        "459": "FFI",
        "461": "FFI",
        "471": "6th Max",
        "473": "FFI",
        "483": "FFI",
        "493": "FFI",
        "499": "FFI",
        "506": "FFI",
        "516": "FFI",
        "522": "5th Max",
        "537": "FFI",
        "539": "FFI",
        "541": "2nd Max",
        "545": "FFI",
        "546": "FFI",
        "553": "FFI",
        "559": "FFI",
        "561": "FFI",
        "578": "5th Max",
        "589": "FFI",
        "590": "FFI",
        "591": "FFI",
        "602": "2nd Max",
        "607": "6th Max",
        "614": "7th Max",
        "621": "6th Max",
        "626": "FFI",
        "628": "3rd Max",
        "631": "6th Max",
        "632": "FFI",
        "637": "FFI",
        "647": "FFI",
        "649": "2nd Max",
        "652": "5th Max",
        "653": "7th Max",
        "655": "FFI",
        "656": "FFI",
        "660": "5th Max",
        "672": "FFI",
        "673": "3rd Max",
        "674": "FFI",
        "683": "7th Max",
        "685": "5th Max",
        "688": "2nd Max",
        "696": "FFI",
        "701": "2nd Max",
        "702": "7th Max",
        "705": "5th Max",
        "706": "FFI",
        "710": "FFI",
        "725": "FFI",
        "727": "FFI",
        "728": "7th Max",
        "732": "7th Max",
        "736": "5th Max",
        "743": "3rd Max",
        "753": "FFI",
        "756": "FFI",
        "761": "6th Max",
        "764": "FFI",
        "766": "FFI",
        "770": "7th Max",
        "773": "6th Max",
        "777": "3rd Max",
        "780": "4th Max",
        "785": "FFI",
        "787": "4th Max",
        "791": "FFI",
        "792": "3rd Max",
        "795": "7th Max",
        "803": "7th Max",
        "805": "FFI",
        "809": "FFI",
        "810": "FFI",
        "817": "FFI",
        "818": "FFI",
        "826": "7th Max",
        "832": "5th Max",
        "844": "FFI",
        "854": "FFI",
        "858": "FFI",
        "867": "7th Max",
        "868": "FFI",
        "869": "FFI",
        "873": "6th Max",
        "874": "4th Max",
        "876": "6th Max",
        "908": "4th Max",
        "909": "FFI",
        "918": "4th Max",
        "922": "FFI",
        "923": "4th Max",
        "930": "FFI",
        "941": "FFI",
        "949": "7th Max",
        "959": "FFI",
        "962": "FFI",
        "966": "FFI",
        "971": "FFI",
        "972": "FFI",
        "976": "FFI",
        "977": "FFI",
        "980": "FFI",
        "982": "6th Max",
        "988": "5th Max",
        "989": "FFI",
        "994": "3rd Max",
        "997": "FFI",
    }
}
