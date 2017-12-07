import unittest

# from . import main
import main


class TestClient(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        self.client = main.app.test_client()

    def test_root(self):
        r = self.client.get('/')
        assert r.status_code == 200
        assert 'Welcome' in r.data.decode('utf-8')

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
