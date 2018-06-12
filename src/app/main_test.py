# TODO: migrate to nose or pytest
import json
import unittest
import logging

# from . import main
import main

logger = logging.getLogger(__name__)

class TestClient(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        self.client = main.app.test_client()

    def test_root(self):
        r = self.client.get('/')
        assert r.status_code == 200
        assert 'Welcome' in r.data.decode('utf-8')

    def test_get_image_urls(self):
        input = {
            "dataset": "bathymetry_jetski",
            "begin_date": "2011-08-01",
            "end_date": "2011-09-01",
            "step": 30,
            "interval": 30,
            "unit": "day"
        }
        r = self.client.post('/get_image_urls', data=json.dumps(input), content_type='application/json')
        logger.debug(r)
        assert r.status_code == 200

    def test_get_bathymetry(self):
        input = {
            "dataset": "vaklodingen",
            "begin_date": "2011-08-01",
            "end_date": "2011-09-01"
        }
        r = self.client.get('/get_bathymetry', data=json.dumps(input), content_type='application/json')
        logger.debug(r)
        assert r.status_code == 200

    def test_get_raster_profile(self):
        line = '''{
        "dataset": "bathymetry_jetski",
        "begin_date": "2011-08-02",
        "end_date": "2011-09-02",
        "polyline": {
              "geodesic": true,
              "type": "LineString",
              "coordinates": [
                [
                  5.03448486328125,
                  53.53541058046374
                ],
                [
                  5.58380126953125,
                  53.13029407190636
                ]
              ]
            },
        "scale": 100
        }'''

        r = self.client.post('/get_raster_profile', data=line, content_type='application/json')
        assert r.status_code == 200

    def test_get_catchments(self):
        request = '''{
            "bounds":
                {"type": "Polygon", "coordinates":
                    [[[5.995833, 4.387513999999975], [7.704733999999998, 4.387513999999975],
                      [7.704733999999998, 7.925567000000025], [5.995833, 7.925567000000025],
                      [5.995833, 4.387513999999975]]]},
            "type": "get_catchments",
            "dissolve": true
        }'''

        r = self.client.post('/get_catchments', data=request, content_type='application/json')
        assert r.status_code == 200

    def test_get_rivers(self):
        request = '''{
            "bounds":
                {"type": "Polygon", "coordinates":
                    [[[5.995833, 4.387513999999975], [7.704733999999998, 4.387513999999975],
                      [7.704733999999998, 7.925567000000025], [5.995833, 7.925567000000025],
                      [5.995833, 4.387513999999975]]]},
            "type": "get_rivers",
            "filter_upstream_gt": 1000
        }'''

        r = self.client.post('/get_rivers', data=request, content_type='application/json')
        assert r.status_code == 200

    def test_get_lakes(self):
        request = '''{
            "bounds":
                {"type": "Polygon", "coordinates":
                    [[[5.995833, 4.387513999999975], [7.704733999999998, 4.387513999999975],
                      [7.704733999999998, 7.925567000000025], [5.995833, 7.925567000000025],
                      [5.995833, 4.387513999999975]]]},
            "type": "get_lakes"
        }'''

        r = self.client.post('/get_lakes', data=request, content_type='application/json')

        print('LAKES: ')
        print(r)

        assert r.status_code == 200

    def test_get_raster(self):
        r = self.client.get('/')
        assert r.status_code == 200

        # r = client.get('/get_catchments')
        # assert r.status_code == 200
        # assert 'Welcome' in r.data.decode('utf-8')


if __name__ == '__main__':
    unittest.main()
