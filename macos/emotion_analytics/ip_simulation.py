"""
NeurodataLab LLC 09.12.2019
Created by Andrey Belyaev
"""
import argparse
from ndlapi.api import create_credentials, get_service_by_name, images_services_list
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

from streaming_processing import GstServer


def parse():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--keys-path', required=True, type=str,
                        help='Path to folder with keys downloaded from api.neurodatalab.dev')
    parser.add_argument('--service', required=True, type=str,
                        help='Service to process video')

    parser.add_argument('--api-url', default='ru1.recognition.api.neurodatalab.dev', type=str, help=argparse.SUPPRESS)
    parser.add_argument('--api-port', default='30051', type=str, help=argparse.SUPPRESS)

    return parser.parse_args()


if __name__ == '__main__':
    # Parse command line arguments
    args = parse()
    assert args.service in ('er', 'EmotionRecognition'), \
        'There are no implementation of IP simulation using %s' % args.service

    # Create ssl authorization token
    ssl_auth = create_credentials(args.keys_path, api_url=args.api_url, api_port=args.api_port)
    # Create service
    service = get_service_by_name(args.service, ssl_auth)

    loop = GObject.MainLoop()
    GObject.threads_init()
    Gst.init(None)

    server = GstServer(service)
    loop.run()
