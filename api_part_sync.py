import pathlib
import typing as tp
from os.path import join


import requests
from bs4 import BeautifulSoup


class SearchEngine:
    """
    Class that search movie or series by given query. Query should be a movie or series name. at least a description,
    like "Фильм про мужчину с собакой про зомби" -> "Я - легенда", in other cases, bot will find nothing.
    """
    def __init__(self) -> None:
        """
        Read and store kinopoisk token from secret file
        """
        self.last_id = "_nothing_"
        self.last_type = "_nothing_"
        current_dir = pathlib.Path(__file__).parent.resolve()
        with open(join(current_dir, join("secrets", "kinopoisk_token.txt")), 'r') as token_file:
            self.token = token_file.readline()

    def _get_id_by_query(self, query: str) -> str | tuple[int, str]:
        """
        Return kinopoisk id of a given query if it's possible, in other case, return -1 and sorry message
        :param query: Movie's or series' name or description if you want a good result.
        :return: given movie's or series' id on kinopoisk, in the case of failure, -1 and sorry message
        """
        url = f"https://www.google.com/search?q={query}+site%3Akinopoisk.ru"
        result = requests.get(url)
        html_text = result.text
        idx = html_text.find('kinopoisk.ru/series/')
        if idx == -1:
            # не нашёл в выдачи нужный префикс.
            idx = html_text.find('kinopoisk.ru/film/')
            if idx == -1:
                # не нашёл ни фильм, ни сериал
                return -1, "Извините, я ничего не нашёл по этому запросу 😿"
            else:
                shift = 40
                ans = result.text[idx:idx + shift]
                query_id = ans.split('/')[2]
                try:
                    int(query_id)
                except ValueError:
                    return -1, "Извините, я ничего не нашёл по этому запросу 😿"
                else:
                    self.last_type = "film"
                    self.last_id = query_id
                    return query_id
        else:
            shift = 40
            ans = result.text[idx:idx + shift]
            query_id = ans.split('/')[2]
            try:
                int(query_id)
            except ValueError:
                return -1, "Извините, я ничего не нашёл по этому запросу 😿"
            else:
                self.last_type = "series"
                self.last_id = query_id
                return query_id

    def get_last_id(self) -> str:
        """
        return last found id
        :return:
        """
        return self.last_id

    def get_last_type(self) -> str:
        """
        return last found id
        :return:
        """
        return self.last_type

    def _get_movie_by_id(self, query_id: str) -> dict[str, tp.Any]:
        """
        Return movie's or series' information from kinopoisk by its id
        :param query_id: movie's or series' id from kinopoisk
        :return: json with show's name, poster, rating, description and legal links to view
        """
        with requests.Session() as session:
            url = "https://api.kinopoisk.dev/movie"
            params = {'token': self.token, 'search': f'{query_id}', 'field': 'id',
                      'selectFields': 'name poster rating description watchability'}
            with session.get(url, params=params) as response:
                return response.json()

    def get_information_by_query(self, query: str) -> dict[str, tp.Any] | tuple[int, str]:
        """
        Return information about query if it's a valid movie or series or at least description
        :param query: given by user query, should be movie's or series' name or at least description
        :return: json with show's name, poster, rating, description and links to view
        """
        query_id = self._get_id_by_query(query)
        if isinstance(query_id, tuple):
            # ничего не нашли
            return query_id[0], query_id[1]
        search_result = self._get_movie_by_id(query_id)
        return search_result

    #  Почему-то ссылки битые почти на всё, кроме jut.su и разных других аниме-сайтов,
    #  оставляю здесь в качестве артефакта.
    @staticmethod
    def get_pirated_links(title: str) -> tuple[list[str], list[str]]:
        """
        Return a list or illegal or just free link to view a show with given title
        :param title: movie's or series' title
        :return: tuple with websites' names and their urls
        """
        # всё как в жизни
        query = {'q': f"{title} смотреть бесплатно онлайн"}
        url = "https://www.google.com/search?"
        html = requests.get(url, params=query).text
        soup = BeautifulSoup(html, features="lxml")
        html = soup.html
        links = html.findAll('a')  # type: ignore
        valid_links = [link for link in links if 'url' in str(link)]

        # заберём пачку ссылок в бот.
        result_names: list[str] = []
        result_links: list[str] = []
        for i in range(len(valid_links)):
            if len(result_links) >= 4:
                break
            current_name = valid_links[i]['href'].split('/')[3]
            if current_name not in result_names:
                result_names.append(current_name)
                result_links.append(valid_links[i]['href'][7:])

        return result_names, result_links


if __name__ == "__main__":
    search_engine = SearchEngine()
    result = search_engine.get_information_by_query("Брат")
    print(result)