from flask import Flask, jsonify, request

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db as db1
app = Flask(__name__)








cred = credentials.Certificate("D:\\recipe_backend\\recipe-c9394-firebase-adminsdk-7e9i5-5713592fbb.json")
firebase_admin.initialize_app(cred)




db=firestore.client()



def get_all_names():
    return {i.to_dict()['name']:i.id for i in db.collection('recipes').get()}



def price_update(np, sn_id):

    cn =  db.collection("recipes").document(sn_id).get().to_dict()
    db.collection("recipes").document(sn_id).update({'price': np})

    q=[[sn_id,np,cn['price']]]
    print(cn)
    while q:
        [curr_id,np,op]=q.pop(0)
        cn = db.collection("recipes").document(curr_id).get().to_dict()
        for i in cn['parents']:
            v = db.collection("recipes").document(i).get().to_dict()
            op1 = v['price']
            print(type(op1),type(np),op,type(v['children'][curr_id]))
            if type(op)==type('abc'):
                op = float(op)
            np1 = op1 + (np-op)*(v['children'][curr_id])
            db.collection("recipes").document(i).update({'price': np1})
            q.append([i,np1,op1])



@app.route('/insert')
def insert_recipe():

    to_insert = request.get_json()
    recipes = [i.to_dict()['name'] for i in db.collection('recipes').get()]

    if to_insert['name'].lower() in recipes:
        return 'already there'


    if 'children' not in to_insert or len(to_insert['children'])==0:
        doc_ref = db.collection(u'recipes').document()
        doc_ref.set({'name':to_insert['name'].lower(),'price':to_insert['price'],'unit':to_insert['unit'],'children':[],'parents':[]})
        id = doc_ref.id
    else:
        price=0
        children=to_insert['children']
        doc_ref = db.collection(u'recipes').document()
        doc_ref.set({'name':to_insert['name'].lower(),'unit':to_insert['unit'],'children':to_insert['children'],'parents':[]})
        id = doc_ref.id
        
        for i in children:
            parents=db.collection('recipes').document(i).get().to_dict()['parents']
            parents.append(id)
            db.collection("recipes").document(i).update({'parents': parents[:]})
            child_price=db.collection('recipes').document(i).get().to_dict()['price']
            price+=children[i]*child_price
        db.collection("recipes").document(id).update({'price': price})
    return 'insert successful'





@app.route('/show/<doc_id>')
def show_recipe(doc_id):
    print(doc_id)
    recipe_ref = db.collection(u'recipes').document(doc_id).get()
    return jsonify({'id':recipe_ref.id,'recipe':db.collection(u'recipes').document(doc_id).get().to_dict()})



@app.route('/delete/<tid>')
def delete(tid):

    cn = db.collection("recipes").document(tid).get().to_dict()

    if not cn:
        return 'recipe does not exist'
    for i in cn['children']:
        child = db.collection("recipes").document(i).get().to_dict()
        db.collection("recipes").document(i).update({'parents': list(filter(lambda x: x != tid,child['parents']))})
    
    price_update(0,tid)

    for i in cn['parents']:
        par = db.collection("recipes").document(i).get().to_dict()
        par['children'].pop(tid)
        db.collection("recipes").document(i).update({'children':par['children']})
    
    return 'deleted'
        





@app.route('/update/<tid>')
def update_recipe(tid):
    old=db.collection(u'recipes').document(tid).get().to_dict()
    print('old:',old)
    msg=''
    if not old:
        return 'id incorrect '
    to_update = request.get_json()
    if old['name']!=to_update['name'] or old['unit']!=to_update['unit']:
        if to_update['name'] in get_all_names():
            msg+='name already exists hence not updated,'
        else:
            db.collection("recipes").document(tid).update({'unit': to_update['unit'], 'name': to_update['name']})

    if old['price']!=to_update['price']:
        if len(old['children'])==0 and len(to_update['children'])==0:
            # db.collection("recipes").document(tid).update({'price': to_update['price']})
            price_update(to_update['price'], tid)

    if old['children']!=to_update['children']:
        np=0
        #decouple old children
        for i in old['children']:
            old_kid = db.collection("recipes").document(i).get().to_dict()
            db.collection("recipes").document(i).update({'parents': list(filter(lambda x: x != i,old_kid['parents'] ))})
        
        #pair up new kids and update the new parent
        for i in to_update['children']:
            new_kid = db.collection("recipes").document(i).get().to_dict()
            np+=new_kid['price']*(to_update['children'][i])
            db.collection("recipes").document(i).update({'parents': new_kid['parents']+[i]})
        db.collection("recipes").document(tid).update({'children':to_update['children']})
        price_update(np,tid)
    
 



    return jsonify({'msg':'recipe updated successfully','not done stuff':msg,'new data':db.collection(u'recipes').document(tid).get().to_dict()})


if __name__ == "__main__":
    app.run()





# print(show_recipe('4Q9AsvnKh9mrqYMkmw5r'))
# update_recipe('4Q9AsvnKh9mrqYMkmw5r', {'children': {'Ibm1XP6XrUYdjj8P1dpp':4}, 'unit': 'gram', 'name': 'f', 'price': 0, 'parents': ['yKrBHEM4TtfJRs8LXBZM']})
# print(show_recipe('4Q9AsvnKh9mrqYMkmw5r'))
