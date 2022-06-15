name_to_dir = {
  'matrix': 'matrix-omp',
  'dotproduct': 'dotproduct-omp',
}

name_to_input_index = {
        'matrix': {
            'test': 'test',
            },
        'dotproduct': {
            'test': 'test'
            },
}

def allbenchmarks():
  return map(lambda x: x[0], sorted(name_to_dir.iteritems(), key=lambda x: x[1]))
