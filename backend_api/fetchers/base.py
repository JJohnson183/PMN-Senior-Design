#============================= Fetcher ==============================#
# Shared parent for every kind of site: each kind turns a site's URL into meetings its own way
class Fetcher:
    # Fetch the site's meetings (a list of Meeting, or None if the site couldn't be read)
    def fetch(self, url):
        # Each kind of site replaces this with its own fetch, so reaching here means one is missing
        raise NotImplementedError(f"{type(self).__name__} has no fetch method")
