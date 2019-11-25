#!/bin/bash
set -x

# create a relationship (both directions)
http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","damian"]' relationship=friends direction=mutual delta=1000
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# update a relationship (single direction)
http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship uuids:='["taylor","damian"]' relationship=friends direction=discrete delta=234
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# create a relationship (single direction)
http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","ninja"]' relationship=influencers direction=discrete delta=100

# get all 'outgoing' relationships for this user 
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor

# get only score for single relationship
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/influencers/ninja

# create a second relationship on the same 'scale'
http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual delta=1000
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph

# delete a relationship (single direction)
http -b --pretty=format DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship uuids:='["taylor","damian"]' relationship=friends direction=discrete
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends

# update a relationship (both directions)
http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual delta=10
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph/friends

# delete a relationship (both directions)
http -b --pretty=format DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship uuids:='["taylor","joseph"]' relationship=friends direction=mutual
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph
