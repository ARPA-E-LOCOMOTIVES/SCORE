# Copyright (c) 2022, The Pennsylvania State University
# All rights reserved.

from rest_framework.exceptions import APIException

class OptimalLPException(APIException):
    status_code = 400
    default_detail = "Optimal LP solution failed"
    default_code = "optimal_lp_failed"