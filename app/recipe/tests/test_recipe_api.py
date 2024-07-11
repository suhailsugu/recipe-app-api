

from decimal import Decimal
from django.contrib.auth import get_user_model

from django.test import TestCase

from django.urls import reverse
from rest_framework import status # type: ignore
from rest_framework.test import APIClient # type: ignore

from core.models import (
    Recipe,
    Tag,
    Ingredient,
    )
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
    )
import tempfile,os
from PIL import Image #type:ignore


RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail',args=[recipe_id])

def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image',args=[recipe_id])



def create_recipe(user,**params):

    defaults = {
        "title" : "Sample recipe API",
        "time_minutes" : 22,
        "price":Decimal('5.25'),
        "description" : "Sample description",
        "link" : 'http://example.com/recipe.pdf',
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user,**defaults)

    return recipe

def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = create_user(email='user@example.com', password='test123')

        self.client.force_authenticate(self.user)


    def test_retrieve_recipe(self):
        create_recipe(user=self.user)
        create_recipe(user=self.user)


        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes,many=True)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)


    def test_recipe_list_limited_user(self):
        other_user = create_user(email='other@example.com', password='test123')


        create_recipe(user=other_user)
        create_recipe(user=self.user)


        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes,many=True)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)


    def test_get_recipe_details(self):

        recipe        = create_recipe(user=self.user)

        url           = detail_url(recipe.id)

        res           = self.client.get(url)

        serializer    = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data,serializer.data)


    def test_create_recipe(self):

        payload = {
          "title" : "Sample recipe API",
          "time_minutes" : 22,
          "price":Decimal('5.25'),
        }

        res = self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data.get('id'))

        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)

        self.assertEqual(recipe.user,self.user)


    def test_partial_update(self):
        """Test partial update of a recipe."""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update(self):
        """Test full update of recipe."""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://exmaple.com/recipe.pdf',
            description='Sample recipe description.',
        )

        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)


    def test_delete_recipe(self):
        """Test deleting a recipe successful."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())


    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tag."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)

        payload = {'tags':[{'name':'Lunch'}]}

        url  = detail_url(recipe.id)

        res = self.client.patch(url , payload , format='json')
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user,name='Lunch')
        self.assertIn(new_tag,recipe.tags.all())


    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user,name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user,name='Lunch')
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)

        res =self.client.patch(url,payload,format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertIn(tag_lunch,recipe.tags.all())
        self.assertNotIn(tag_breakfast,recipe.tags.all())


    def test_clear_recipe__tag(self):
        tag_breakfast = Tag.objects.create(user=self.user,name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {'tags':[]}
        url = detail_url(recipe.id)

        res =self.client.patch(url,payload,format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(),0)


    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new Ingredients."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'ingredient': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredient.count(), 2)
        for ingredient in payload['ingredient']:
            exists = recipe.ingredient.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_ingreidents(self):
        """Test creating a recipe with existing Ingredient."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Chilly')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'ingredient': [{'name': 'Chilly'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredient.count(), 2)
        self.assertIn(ingredient1, recipe.ingredient.all())
        for ingredient in payload['ingredient']:
            exists = recipe.ingredient.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_ingredient_on_update(self):

        recipe = create_recipe(user=self.user)

        payload = {'ingredient':[{'name':'Limes'}]}
        url = detail_url(recipe.id)
        res= self.client.patch(url,payload,format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user,name='Limes')
        self.assertIn(new_ingredient,recipe.ingredient.all())


    def test_update_recipe_assign_ingredient(self):
        ingredient1 = Ingredient.objects.create(user=self.user,name='Chilly')
        recipe = create_recipe(user=self.user)
        recipe.ingredient.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user,name='Lunch')
        payload = {'ingredient':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)

        res =self.client.patch(url,payload,format='json')


        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertIn(ingredient2,recipe.ingredient.all())
        self.assertNotIn(ingredient1,recipe.ingredient.all())


    def test_clear_recipe_ingredients(self):
        ingredient1 = Ingredient.objects.create(user=self.user,name='Chilly')
        recipe = create_recipe(user=self.user)
        recipe.ingredient.add(ingredient1)

        payload = {'ingredient':[]}
        url = detail_url(recipe.id)

        res =self.client.patch(url,payload,format='json')

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(recipe.ingredient.count(),0)


    def test_filter_by_tags(self):
        r1 = create_recipe(user=self.user,title='Thai')
        r2 = create_recipe(user=self.user,title='Augbernie')
        tag1 = Tag.objects.create(user=self.user,name='Vegan')
        tag2 = Tag.objects.create(user=self.user,name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_recipe(user=self.user,title='Fish and Chips')

        params = {'tags':f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL,params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data,res.data)
        self.assertIn(s2.data,res.data)
        self.assertNotIn(s3.data,res.data)

    def test_filter_by_ingredients(self):
        r1 = create_recipe(user=self.user,title='Thai')
        r2 = create_recipe(user=self.user,title='Augbernie')

        ing1 = Ingredient.objects.create(user=self.user,name='chilli')
        ing2 = Ingredient.objects.create(user=self.user,name='salt')

        r1.ingredient.add(ing1)
        r2.ingredient.add(ing2)

        r3 = create_recipe(user=self.user,title='Fish and chips')

        params = {'ingredients':f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPES_URL,params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data,res.data)
        self.assertIn(s2.data,res.data)
        self.assertNotIn(s3.data,res.data)

















class ImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com',password='testpass123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):

        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img  = Image.new('RGB',(10,10))
            img.save(image_file,format='JPEG')
            image_file.seek(0)
            payload = {'image':image_file}

            res =self.client.post(url,payload,format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertIn('image',res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)











