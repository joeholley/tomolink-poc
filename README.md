# Tomolink POC
This is all subject to change before the final version.

## Files
**app.py**

The main API definition and related code.  It's using the Python Flask framework.  The final version is planning to use golang.

**cloudbuild.yaml**

A file that defines a Google Cloud Build job. I have an internal PoC repo set up that has a commit hook that automatically kicks off all the jobs in this file.  Basically all it does is packages up the flask app in a container, pushes that container to Google Cloud, and tells Cloud Run (the fully managed Google CLoud Platform serverless product) to run that container.  Deploys take about 1 minute from the time of commit using this file.

**Dockerfile**

Docker container definition file.

**requirements.txt**

List of the python modules being used by the app. Note: I don't really try to keep this clean since this PoC code is going away anyway.  There may be modules listed here that aren't in use in the actual app anymore.

## Quickstart
These command are using [httpie](https://httpie.org/) to make the HTTP requests, because it is stupid easy, but you can use any tool you like. These commands are all in the bash script `cmd.sh` in the root directory of the repository for reference.


```
# create a relationship (both directions)
+ http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship 'uuids:=["taylor","damian"]' relationship=friends direction=mutual delta=1000
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
{
    "results": {
        "friends": {
            "damian": 1000
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends
{
    "results": {
        "friends": {
            "taylor": 1000
        }
    },
    "success": true
}
```
```
# update a relationship (single direction)
+ http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship 'uuids:=["taylor","damian"]' relationship=friends direction=discrete delta=234
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
{
    "results": {
        "friends": {
            "damian": 1234
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends
{
    "results": {
        "friends": {
            "taylor": 1000
        }
    },
    "success": true
}
```
```
# create a relationship (single direction)
+ http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship 'uuids:=["taylor","ninja"]' relationship=influencers direction=discrete delta=100
{
    "success": true
}
```
```
# get all 'outgoing' relationships for this user 
+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
{
    "results": {
        "friends": {
            "damian": 1234
        },
        "influencers": {
            "ninja": 100
        }
    },
    "success": true
}
```
```
# get only score for single relationship
+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/influencers/ninja
{
    "results": 100,
    "success": true
}
```
```
# create a second relationship on the same 'scale'
+ http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/createRelationship 'uuids:=["taylor","joseph"]' relationship=friends direction=mutual delta=1000
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
{
    "results": {
        "friends": {
            "damian": 1234,
            "joseph": 1000
        },
        "influencers": {
            "ninja": 100
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph
{
    "results": {
        "friends": {
            "taylor": 1000
        }
    },
    "success": true
}
```
```
# delete a relationship (single direction)
+ http -b --pretty=format DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship 'uuids:=["taylor","damian"]' relationship=friends direction=discrete
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
{
    "results": {
        "friends": {
            "joseph": 1000
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/damian/friends
{
    "results": {
        "friends": {
            "taylor": 1000
        }
    },
    "success": true
}
```
```
# update a relationship (both directions)
+ http -b --pretty=format POST https://tomolink-poc-studqxcyea-an.a.run.app/updateRelationship 'uuids:=["taylor","joseph"]' relationship=friends direction=mutual delta=10
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor/friends
{
    "results": {
        "friends": {
            "joseph": 1010
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph/friends
{
    "results": {
        "friends": {
            "taylor": 1010
        }
    },
    "success": true
}
```
```
# delete a relationship (both directions)
+ http -b --pretty=format DELETE https://tomolink-poc-studqxcyea-an.a.run.app/deleteRelationship 'uuids:=["taylor","joseph"]' relationship=friends direction=mutual
{
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/taylor
{
    "results": {
        "friends": {},
        "influencers": {
            "ninja": 100
        }
    },
    "success": true
}

+ http -b --pretty=format GET https://tomolink-poc-studqxcyea-an.a.run.app/users/joseph
{
    "results": {
        "friends": {}
    },
    "success": true
}
```
