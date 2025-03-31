# TODO:
# Sorts as at

end = {
    "data": {
        "type": "tala.model.domain.Domain",
        "id": "mockup_domain",
        "version:id": "2",
        "relationships": {
            "plans": [{
                "data": {
                    "type": "tala.model.plan",
                    "id": "mockup_domain:resolve:price"
                }
            }]
        },
    },
    "included": [{
        "type": "tala.model.plan",
        "id": "mockup_domain:resolve:price",
        "version:id": "2",
        "attributes": {
            "ontology_name": "mockup_ontology",
            "name": "paris"
        },
        "relationships": {
            "content": {
                "data": [{
                    "type": "tala.model.plan_item",
                    "id": "greet"
                }, {
                    "type": "tala.model.plan_item",
                    "id": "mockup_ontology:assume:some_predicate:some_individual"
                }]
            }
        },
        "included": [{
            "type": "tala.model.plan_item",
            "id": "greet",
            "version:id": "2",
            "attributes": {},
            "relationships": {}
        }, {
            "type": "tala.model.plan_item",
            "id": "mockup_ontology:assume:some_predicate:some_individual",
            "version:id": "2",
            "attributes": {},
            "relationships": {
                "content": {
                    "data": {
                        "type": "tala.model.proposition",
                        "id": "some_predicate:some_individual"
                    }
                }
            }
        }, {
            "type": "tala.model.sort",
            "id": "mockup_ontology:city",
            "attributes": {
                "version:id": "2",
                "ontology_name": "mockup_ontology",
                "name": "city",
                "dynamic": False
            }
        }]
    }]
}

input = {
    "data": [{
        "type": "tala.model.domain.Domain",
        "id": "mockup_ddd",
        "attributes": {
            "user_defined_name": "Domain Name",
            "id": "tala.model.domain.Domain.user_defined_name",
            "version:id": "2",
        },
        "relationships": [{
            "type": "tala.model.domain.Domain.default_question",
            "id": "tala.model.domain.Domain.default_question",
            "version:id": "2",
            "attributes": [],
            "relationships": {
                "default_question": {
                    "data": {
                        "type": "tala.model.question.WhQuestion",
                        "id": "mockup_ontology:WHQ:X.dest_city(X)",
                        "version:id": "2",
                        "attributes": {
                            "ontology_name": "mockup_ontology",
                            "type": "WHQ"
                        },
                        "relationships": {
                            "content": {
                                "data": {
                                    "type": "LambdaAbstractedPredicateProposition",
                                    "id": "X.dest_city(X)",
                                    "version:id": "2",
                                    "relationships": {
                                        "predicate": {
                                            "data": {
                                                "type": "tala.model.predicate",
                                                "id": "mockup_ontology:dest_city",
                                                "version:id": "2",
                                                "attributes": {
                                                    "ontology_name": "mockup_ontology",
                                                    "name": "dest_city"
                                                },
                                                "relationships": {
                                                    "sort": {
                                                        "data": {
                                                            "type": "tala.model.sort",
                                                            "id": "mockup_ontology:city",
                                                            "version:id": "2",
                                                            "attributes": {
                                                                "ontology_name": "mockup_ontology",
                                                                "name": "city",
                                                                "dynamic": True
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }]
    }]
}

output = {
    "data": [{
        "type": "tala.model.domain.Domain",
        "id": "mockup_ddd",
        "attributes": {
            "version:id": "2",
            "user_defined_name": "MockDDD"
        },
        "relationships": [{
            "type": "tala.model.domain.Domain.default_question",
            "id": "tala.model.domain.Domain.default_question",
            "version:id": "2",
            "attributes": [],
            "relationships": {
                "default_question": {
                    "data": {
                        "type": "tala.model.question.WhQuestion",
                        "id": "mockup_ontology:WHQ:X.dest_city(X)"
                    }
                }
            }
        }]
    }],
    "included": [{
        "type": "tala.model.question.WhQuestion",
        "id": "mockup_ontology:WHQ:X.dest_city(X)",
        "version:id": "2",
        "attributes": {
            "ontology_name": "mockup_ontology",
            "type": "WHQ"
        },
        "relationships": {
            "content": {
                "data": {
                    "type": "LambdaAbstractedPredicateProposition",
                    "id": "X.dest_city(X)",
                }
            }
        }
    }, {
        "type": "LambdaAbstractedPredicateProposition",
        "id": "X.dest_city(X)",
        "version:id": "2",
        "relationships": {
            "predicate": {
                "data": {
                    "type": "tala.model.predicate",
                    "id": "mockup_ontology:dest_city",
                }
            }
        }
    }, {
        "type": "tala.model.predicate",
        "id": "mockup_ontology:dest_city",
        "attributes": {
            "ontology_name": "mockup_ontology",
            "name": "dest_city"
        },
        "relationships": {
            "sort": {
                "data": {
                    "type": "tala.model.sort",
                    "id": "city"
                }
            }
        }
    }, {
        "type": "tala.model.sort",
        "id": "city",
        "attributes": {
            "ontology_name": "mockup_ontology",
            "name": "city",
            "dynamic": True
        }
    }]
}

s = {
    'data': [{
        'type': 'tala.model.ontology',
        'id': 'mockup_ontology',
        'version:id': '2',
        'attributes': {
            'ontology_name': 'mockup_ontology',
            'individuals': [],
            'actions': []
        },
        'relationships': {
            'predicates': {
                "data": [{
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:third predicate',
                }, {
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:first predicate',
                }, {
                    'type': 'tala.model.predicate',
                    'id': 'second predicate',
                }],
            }
        }
    }],
    'included': [{
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:another sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'real',
        'attributes': {
            'version:id': '2',
            'name': 'real',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:third predicate',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'id': 'third predicate'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:another sort'
                }
            }
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:first predicate',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'id': 'first predicate'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:sort'
                }
            }
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'second predicate',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'id': 'second predicate'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'real'
                }
            }
        }
    }]
}

t = {
    'data': [{
        'type': 'tala.model.ontology',
        'id': 'mockup_ontology',
        'version:id': '2',
        'attributes': {
            'ontology_name': 'mockup_ontology',
            'id': 'mockup_ontology',
            'predicates': [{
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:another predicate 1',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'another predicate 1'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:another sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:a predicate 2',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'a predicate 2'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:another predicate 2',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'another predicate 2'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:another sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:a predicate 1',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'a predicate 1'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }],
            'individuals': [{
                'type': 'tala.model.individual',
                'id': 'mockup_ontology:individual',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'individual'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }],
            'actions': []
        },
        'relationships': {}
    }],
    'included': [{
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:another sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:another sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }]
}

u = {
    'data': [{
        'type': 'tala.model.ontology',
        'id': 'mockup_ontology',
        'version:id': '2',
        'attributes': {
            'ontology_name': 'mockup_ontology',
            'name': 'mockup_ontology'
        },
        'relationships': {
            'predicates': [{
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:another predicate 2',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'another predicate 2'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:another sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:a predicate 1',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'a predicate 1'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:another predicate 1',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'another predicate 1'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:another sort'
                        }
                    }
                }
            }, {
                'type': 'tala.model.predicate',
                'id': 'mockup_ontology:a predicate 2',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'a predicate 2'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }],
            'sorts': [{
                'type': 'tala.model.sort',
                'id': 'mockup_ontology:another sort',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'another sort',
                    'dynamic': False
                }
            }, {
                'type': 'tala.model.sort',
                'id': 'mockup_ontology:a sort',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'a sort',
                    'dynamic': False
                }
            }],
            'individuals': [{
                'type': 'tala.model.individual',
                'id': 'mockup_ontology:individual',
                'attributes': {
                    'version:id': '2',
                    'ontology_name': 'mockup_ontology',
                    'name': 'individual'
                },
                'relationships': {
                    'sort': {
                        'data': {
                            'type': 'tala.model.sort',
                            'id': 'mockup_ontology:a sort'
                        }
                    }
                }
            }],
            'actions': []
        }
    }],
    'included': [{
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:another sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:another sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }, {
        'type': 'tala.model.sort',
        'id': 'mockup_ontology:a sort',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a sort',
            'dynamic': False
        }
    }]
}

p = {
    'data': {
        'type': 'tala.model.ontology',
        'id': 'mockup_ontology',
        'version:id': '2',
        'attributes': {},
        'relationships': {
            'predicates': {
                'data': [{
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:a predicate 1'
                }, {
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:a predicate 2'
                }, {
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:another predicate 1'
                }, {
                    'type': 'tala.model.predicate',
                    'id': 'mockup_ontology:another predicate 2'
                }]
            },
            'individuals': {
                'data': [{
                    'type': 'tala.model.individual',
                    'id': 'mockup_ontology:individual'
                }]
            },
            'sorts': {
                'data': []
            },
            'actions': {
                'data': []
            }
        }
    },
    'included': [{
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:a predicate 1',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a predicate 1'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:a sort'
                }
            }
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:a predicate 2',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'a predicate 2'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:a sort'
                }
            }
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:another predicate 1',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another predicate 1'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:another sort'
                }
            }
        }
    }, {
        'type': 'tala.model.predicate',
        'id': 'mockup_ontology:another predicate 2',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'another predicate 2'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:another sort'
                }
            }
        }
    }, {
        'type': 'tala.model.individual',
        'id': 'mockup_ontology:individual',
        'attributes': {
            'version:id': '2',
            'ontology_name': 'mockup_ontology',
            'name': 'individual'
        },
        'relationships': {
            'sort': {
                'data': {
                    'type': 'tala.model.sort',
                    'id': 'mockup_ontology:a sort'
                }
            }
        }
    }]
}
