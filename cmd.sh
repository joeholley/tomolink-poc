#!/bin/bash
set -x

# create a relationship (both directions)
http POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","damian"]' relationship=friends direction=mutual delta=1000
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# update a relationship (single direction)
http POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship uuids:='["taylor","damian"]' relationship=friends direction=discrete delta=234
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# create a relationship (single direction)
http POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","ninja"]' relationship=influencers direction=discrete delta=100

# get all 'outgoing' relationships user has
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor

# get only score for single relationship
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/influencers/ninja

# create a second relationship on the same 'scale'
http POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual delta=1000
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph

# delete a relationship (single direction)
http DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship uuids:='["taylor","damian"]' relationship=friends direction=discrete
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# update a relationship (both directions)
http POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual delta=10
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph/friends

# delete a relationship (both directions)
http DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
http GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph
