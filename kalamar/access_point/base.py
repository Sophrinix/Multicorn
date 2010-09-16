# -*- coding: utf-8 -*-
# This file is part of Dyko
# Copyright © 2008-2009 Kozea
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kalamar.  If not, see <http://www.gnu.org/licenses/>.

"""
Access point base class.

"""

from ..item import Item
from itertools import product
from ..request import And, Condition

class NotOneMatchingItem(Exception):
    """Not one object has been returned."""

class MultipleMatchingItems(NotOneMatchingItem):
    """More than one object have been returned."""

class ItemDoesNotExist(NotOneMatchingItem):
    """No object has been returned."""


DEFAULT_PARAMETER = object()

class AccessPoint(object):
    """Abstract class for all access points.

    """
    def open(self, request, default=DEFAULT_PARAMETER):
        """Return the item in access_point matching request.
        
        If there is no result, raise ``Site.ObjectDoesNotExist``.
        If there are more than one result, raise ``Site.MultipleObjectsReturned``.
        
        """
        results = iter(self.search(request))
        try:
            item = results.next()
        except StopIteration:
            if default is DEFAULT_PARAMETER:
                raise ItemDoesNotExist
            return default
        
        try:
            results.next()
        except StopIteration:
            return item
        else:
            raise MultipleMatchingItems

    def search(self, request):
        """Return an iterable of every item matching request.

        """
        raise NotImplementedError('Abstract method')
    
#    def view(self, request, mapping={}, interval=(0, -1), order=name|tuple(name)|tuple(tuple(name,order))):
    def view(self, view_request, **kwArgs):
        """Returns partial items.

        ``mapping`` is a dict mapping the items property to custom keys in 
        the returned partial items. 

        ``request`` follows the same format as in the search method.
        Example:
        site.view("access_point',{"name":"name","boss_name": "foreign.name"})

        """
        def alias_item(item, aliases):
            return dict([(alias, item[value]) for alias, value in aliases.items()])
        orphan_request = view_request.orphan_request
        fake_props = []

        for item in self.search(view_request.request):
            view_item = alias_item(item,view_request.aliases)
            subitems_generators = []
            for prop, subview in view_request.subviews.items():
                property_obj = self.properties[prop]
                remote_ap = self.site.access_points[property_obj.remote_ap]
                if property_obj.relation == 'many-to-one':
                    for id_prop in remote_ap.identity_properties:
                        fake_prop = '____' + prop + '____' + id_prop
                        fake_props.append(fake_prop)
                        orphan_request = And(orphan_request, Condition(fake_prop, '=', item[prop][id_prop]))
                        subview.aliases[fake_prop] = id_prop
                elif property_obj.relation == 'one-to-many':
                    subview.request = And(Condition(property_obj.remote_property,'=',item),subview.request)
                subitems_generators.append(remote_ap.view(subview))
            if not subitems_generators:
                yield view_item
            else: 
                for cartesian_item in product(*subitems_generators):
                    newitem = dict(view_item)
                    for cartesian_atom in cartesian_item:
                        newitem.update(cartesian_atom)
                        
                        if orphan_request.test(newitem):
                            for fake_prop in fake_props:
                                newitem.pop(fake_prop)
                            yield newitem
        
    def delete_many(self, request):
        """Delete all item matching the request.
        """
        for item in self.search(request):
            self.delete(item)
    
    def delete(self, item):
        """Delete the item from the backend storage.
        
        This method has to be overridden.

        """
        raise NotImplementedError('Abstract method')
    
    def create(self, properties={}):
        """Create a new item.
        
        """
        item = Item(self, properties)
        return item

    def save(self, item):
        """Update or add the item.

        This method has to be overriden.

        """
        raise NotImplementedError('Abstract method')

    @property
    def identity_properties(self):
        raise NotImplementedError('Abstract method')
    

