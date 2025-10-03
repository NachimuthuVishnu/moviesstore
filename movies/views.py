from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Petition, Vote
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import ReviewReport


def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})


def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html', {'template_data': template_data})


@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)


@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)


@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


@login_required
def report_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    ReviewReport.objects.get_or_create(review=review, user=request.user)
    return redirect('movies.show', id=id)


def petitions_index(request):
    petitions = Petition.objects.all().order_by('-created_date')
    
    template_data = {}
    template_data['title'] = 'Movie Petitions'
    template_data['petitions'] = petitions
    return render(request, 'movies/petitions_index.html', {'template_data': template_data})


@login_required
def create_petition(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        movie_title = request.POST.get('movie_title', '').strip()
        
        if title and description and movie_title:
            petition = Petition()
            petition.title = title
            petition.description = description
            petition.movie_title = movie_title
            petition.created_by = request.user
            petition.save()
            messages.success(request, 'Petition created successfully!')
            return redirect('movies.petitions_index')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    template_data = {}
    template_data['title'] = 'Create Petition'
    return render(request, 'movies/create_petition.html', {'template_data': template_data})


def petition_detail(request, petition_id):
    petition = get_object_or_404(Petition, id=petition_id)
    user_vote = None
    
    if request.user.is_authenticated:
        try:
            user_vote = Vote.objects.get(petition=petition, user=request.user)
        except Vote.DoesNotExist:
            pass
    
    template_data = {}
    template_data['title'] = f'Petition: {petition.title}'
    template_data['petition'] = petition
    template_data['user_vote'] = user_vote
    return render(request, 'movies/petition_detail.html', {'template_data': template_data})


@login_required
def vote_petition(request, petition_id):
    petition = get_object_or_404(Petition, id=petition_id)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['yes', 'no']:
        messages.error(request, 'Invalid vote type.')
        return redirect('movies.petition_detail', petition_id=petition_id)
    
    # Check if user already voted
    existing_vote, created = Vote.objects.get_or_create(
        petition=petition, 
        user=request.user,
        defaults={'vote_type': vote_type}
    )
    
    if not created:
        # User already voted, update their vote
        old_vote_type = existing_vote.vote_type
        
        # Update vote counts
        if old_vote_type == 'yes':
            petition.yes_votes -= 1
        else:
            petition.no_votes -= 1
            
        if vote_type == 'yes':
            petition.yes_votes += 1
        else:
            petition.no_votes += 1
            
        existing_vote.vote_type = vote_type
        existing_vote.save()
        petition.save()
        
        messages.success(request, f'Your vote has been updated to {vote_type}.')
    else:
        # New vote
        if vote_type == 'yes':
            petition.yes_votes += 1
        else:
            petition.no_votes += 1
        petition.save()
        
        messages.success(request, f'Thank you for voting {vote_type}!')
    
    return redirect('movies.petition_detail', petition_id=petition_id)