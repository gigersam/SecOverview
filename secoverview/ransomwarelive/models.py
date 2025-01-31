from django.db import models

class RansomwareliveGroupsGroup(models.Model):
    name = models.CharField(max_length=512)
    captcha = models.BooleanField(default=False)
    parser = models.BooleanField(default=False)
    javascript_render = models.BooleanField(default=False)
    meta = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class RansomwareliveVictim(models.Model):
    post_title = models.CharField(max_length=256)
    discovered = models.DateTimeField()
    published = models.DateTimeField()
    post_url = models.URLField(max_length=2048, null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    activity = models.CharField(max_length=2048, null=True, blank=True)
    website = models.URLField(max_length=2048, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    group = models.ForeignKey(RansomwareliveGroupsGroup, on_delete=models.CASCADE, related_name='posts')

    def __str__(self):
        return self.post_title

    @staticmethod
    def get_post_by_title_and_group(post_title, group_id):
        return RansomwareliveVictim.objects.filter(post_title=post_title, group_id=group_id).first()

    @staticmethod
    def add_post(post_data):
        group, _ = RansomwareliveGroupsGroup.objects.get_or_create(name=post_data['group_name'])
        post = RansomwareliveVictim.objects.create(
            post_title=post_data['post_title'],
            discovered=post_data['discovered'],
            published=post_data['published'],
            post_url=post_data.get('post_url', ''),
            country=post_data.get('country', ''),
            activity=post_data.get('activity', ''),
            website=post_data.get('website', ''),
            description=post_data.get('description', ''),
            group=group
        )
        return post

class RansomwareliveGroupsLocation(models.Model):
    group = models.ForeignKey(RansomwareliveGroupsGroup, on_delete=models.CASCADE, related_name='locations')
    fqdn = models.CharField(max_length=2024)
    title = models.CharField(max_length=512, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)
    slug = models.CharField(max_length=2024, null=True, blank=True)
    available = models.BooleanField(default=False)
    updated = models.DateTimeField(null=True, blank=True)
    lastscrape = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.fqdn

    @staticmethod
    def get_location_by_fqdn(fqdn, group_id):
        return RansomwareliveGroupsLocation.objects.filter(fqdn=fqdn, group_id=group_id).first()

    @staticmethod
    def add_location(location_data, group):
        return RansomwareliveGroupsLocation.objects.create(
            fqdn=location_data['fqdn'],
            title=location_data.get('title'),
            version=location_data['version'],
            slug=location_data.get('slug'),
            available=location_data.get('available', False),
            updated=location_data.get('updated'),
            lastscrape=location_data.get('lastscrape'),
            enabled=location_data.get('enabled', False),
            group=group
        )

class RansomwareliveGroupsProfile(models.Model):
    group = models.ForeignKey(RansomwareliveGroupsGroup, on_delete=models.CASCADE, related_name='profiles')
    link = models.URLField(max_length=2048)

    def __str__(self):
        return self.link

    @staticmethod
    def get_profile_by_link(link, group_id):
        return RansomwareliveGroupsProfile.objects.filter(link=link, group_id=group_id).first()

    @staticmethod
    def add_profile(profile_data, group):
        return RansomwareliveGroupsProfile.objects.create(
            link=profile_data,
            group=group
        )