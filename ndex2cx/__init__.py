__author__ = 'aarongary'


def get_status():
    """
    Gets the status
    :return: Message
    :rtype: string
    """
    return 'status good'


known_aspects = [
    'nodes',
    'edges',
    'nodeAttributes',
    'edgeAttributes',
    'networkAttributes',
    'provenanceHistory',
    'citations',
    'nodeCitations',
    'edgeCitations',
    'supports',
    'nodeSupports',
    'edgeSupports',
    'cartesianLayout',
    '@context',
    'cyVisualProperties',
    'visualProperties'
    ]

known_aspects_min = [
    'nodes',
    'edges',
    '@context',
    'nodeAttributes',
    'edgeAttributes',
    'networkAttributes',
    'provenanceHistory'
    ]


if __name__ == '__main__':  # pragma: no cover
    print('in main')
