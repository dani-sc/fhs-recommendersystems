# Load required modules
import csv
import numpy as np
import operator
import scipy.spatial.distance as scidist

# Parameters
UAM_FILE = "./data/UAM.csv"                    # user-artist-matrix (UAM)
ARTISTS_FILE = "./data/UAM_artists.csv"        # artist names for UAM
USERS_FILE = "./data/UAM_users.csv"            # user names for UAM

NEAREST_USERS = 3
MAX_ITEMS_TO_PREDICT = 10

# Function to read metadata (users or artists)
def read_from_file(filename):
    data = []
    with open(filename, 'r') as f:                  # open file for reading
        reader = csv.reader(f, delimiter='\t')      # create reader
        headers = reader.next()                     # skip header
        for row in reader:
            item = row[0]
            data.append(item)
    return data

def simple_recommender_cf(user, UAM, max_items_to_predict, nearest_users_to_consider):
    # user .. the user for whom we want to predict artists for
    # UAM .. user artist matrix
    # max_items_to_predict .. how many artists shall be predicted
    # nearest_users_to_consider .. how many similar users to consider
    pc_vec = UAM[user,:]

    # Compute similarities as inner product between pc_vec of user and all users via UAM (assuming that UAM is already normalized)
    sim_users = np.zeros(shape=(UAM.shape[0]), dtype=np.float32)
    for u in range(0, UAM.shape[0]):
        if (np.max(UAM[u, :]) == 0):
            similarity = 0
        else:
            similarity = 1.0 - scidist.cosine(pc_vec, UAM[u,:])
        sim_users[u] = similarity


    # Sort similarities to all others
    sort_idx = np.argsort(sim_users)        # sort in ascending order

    # Select the  closest neighbors to seed user u (which are the last but one; last one is user u herself!)
    neighbors_idx = sort_idx[-(nearest_users_to_consider+2):-2]
    # for neighbor_idx in neighbors_idx:
        # print "The closest user to user " + str(user) + " are " + str(neighbor_idx) + "."
        # print "The closest user to user " + users[u] + " is user " + users[neighbor_idx] + "."

    # Get list of all neighbors' artist, except those artists from user u
    artist_idx_u = np.nonzero(UAM[user,:])                 # indices of artists user u listened to

    artists = []
    for neighbor_idx in neighbors_idx:
        artist_idx_n = np.nonzero(UAM[neighbor_idx,:])[0].tolist()
        artists += artist_idx_n
    
    artists = np.unique(artists)
    artists = np.setdiff1d(artists, artist_idx_u)

    # Calculate artists' score
    # calculated factors of the artists' scores:
    #   user similarity
    #   playcount of artist
    #   number of users per artist
    # could be further adjusted by adding additional weights
    artists_score = {}
    for artist in artists:
        user_artist_count = 0
        for neighbor_idx in neighbors_idx:
            playcount = UAM[neighbor_idx, artist]
            score = playcount * sim_users[neighbor_idx]
            if artist in artists_score:
                artists_score[artist] += score
            else:
                artists_score[artist] = score
            if playcount > 0:
                user_artist_count += 1

        artists_score[artist] *= float(user_artist_count) / len(neighbors_idx)

    # Normalization
    # scores can be normalized like this:  score_normalized = (score - min) / (max - min)
    # score calculation for our CF is:       score = sum of weighted playcounts of the KNN  * normalized_user_artist_count
    # so the max possible score should be:     max = KNN * 1 * 1
    # the min score should be                  min = 0

    playcounts_total = np.sum(UAM)
    max_score = nearest_users_to_consider
    min_score = 0
    for artist, score in artists_score.items():
        score_normalized = (score - min_score) / (max_score - min_score)
        artists_score[artist] = score_normalized

    # Sort the artists depending on their calculated scores
    sorted_recommended_artists = sorted(artists_score.items(), reverse=True, key=operator.itemgetter(1))[:max_items_to_predict]
    
    dict_rec_aidx = dict(sorted_recommended_artists)

    return dict_rec_aidx

# Main program
if __name__ == '__main__':
    # Load metadata from provided files into lists
    artists = read_from_file(ARTISTS_FILE)
    users = read_from_file(USERS_FILE)

    # Load UAM
    UAM = np.loadtxt(UAM_FILE, delimiter='\t', dtype=np.float32)

    # For all users apply the simple recommender cf
    for user in range(0, UAM.shape[0]):
        # get playcount vector for current user u
        print "Next user recommendations: "
        user_most_listened_to_artists = np.argsort(UAM[user,:])[::-1]
        for i in range(0, 10):
            print str(i+1) + ". rank: " + artists[user_most_listened_to_artists[i]]
        print "- - - - - - - "
        recommended_artists_idx = simple_recommender_cf(user, UAM, MAX_ITEMS_TO_PREDICT, NEAREST_USERS)
        for i in range(0, len(recommended_artists_idx)):
            print str(i+1) + ". rank: " + artists[recommended_artists_idx[i]]
        print "\n"
