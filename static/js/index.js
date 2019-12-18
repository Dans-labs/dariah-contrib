/* eslint-env jquery */

/* global groupRel */

const SAVE = true
const DEBUG = true
const BLUR = true

const emptyS = ''
const emptyO = {}

const widgets = {
  text: {
    activate() {},
    read(elem) {
      return elem.prop('value')
    },
  },
  markdown: {
    activate() {},
    read(elem) {
      return elem.prop('value')
    },
  },
  bool: {
    activate(table, eid, field, parent, valueEl, targets) {
      targets.each((i, elem) => {
        const el = $(elem)
        const options = el.find('[bool]')
        el.find('.icon')
          .off('click')
          .click(e => {
            options.removeClass('active')
            const me = $(e.currentTarget)
            me.addClass('active')
            edit(table, eid, field, valueEl, parent)
          })
      })
    },
    read(elem) {
      const el = elem.find('.active')
      const boolValue = el.attr('bool')
      return boolValue == 'true' ? true : boolValue == 'false' ? false : null
    },
  },
  related: {
    activate(table, eid, field, parent, valueEl, targets) {
      const filterKey = `${table}/${eid}/${field}/filter`
      const multiple = valueEl.attr('multiple')
      const extensible = valueEl.attr('extensible')
      targets.each((i, elem) => {
        const el = $(elem)
        const options = el.find('[lab]')
        el.find('.button,.task')
          .off('click')
          .click(e => {
            const me = $(e.currentTarget)
            if (multiple) {
              if (me.hasClass('active')) {
                me.removeClass('active')
              } else {
                me.addClass('active')
              }
            } else {
              options.removeClass('active')
              me.addClass('active')
            }
            edit(table, eid, field, valueEl, parent)
          })
        const filterControl = el.find('input.wfilter')
        if (filterControl) {
          const filterOff = el.find('.icon.wfilter.clear')
          const filterAdd = el.find('.icon.wfilter.add')
          const prevFilter = localStorage.getItem(filterKey) || ''
          filterControl.val(prevFilter)
          filterTags(options, prevFilter, filterOff, filterAdd, extensible)
          filterControl.off('keyup').on('keyup', () => {
            const curFilter = filterControl.val()
            localStorage.setItem(filterKey, curFilter)
            filterTags(options, curFilter, filterOff, filterAdd, extensible)
          })
          filterOff.off('click').click(() => {
            const newFilter = ''
            filterControl.val(newFilter)
            localStorage.setItem(filterKey, newFilter)
            filterTags(options, newFilter, filterOff, filterAdd, extensible)
          })
          filterAdd.off('click').click(() => {
            const newTag = filterControl.val()
            if (extensible && newTag) {
              edit(table, eid, field, valueEl, parent, newTag)
            }
          })
        }
      })
    },
    read(elem) {
      const el = elem.find('.active')
      return (el && el.attr('eid')) || null
    },
    readMultiple(elem) {
      return $.makeArray(elem.find('.active').map((i, el) => $(el).attr('eid')))
    },
    collapseMultiple: true,
  },
}

const filterTags = (options, pattern, off, add, extensible) => {
  if (pattern) {
    const pat = pattern.toLowerCase()
    let remaining = 0
    options.each((i, elem) => {
      const el = $(elem)
      const lab = el.attr('lab')
      if (lab.indexOf(pat) == -1) {
        el.hide()
      } else {
        el.show()
        remaining++
      }
    })
    off.show()
    if (extensible) {
      if (remaining) {
        add.hide()
      } else {
        add.show()
      }
    } else {
      add.hide()
    }
  } else {
    options.show()
    off.hide()
  }
}

const flash = (task, error) => {
  const msgbar = $('#msgbar')
  const stat = error || 'succeeded'
  const cls = error ? 'error' : 'message'
  msgbar.html(`<div class="msgitem ${cls}">&lt${task}&gt; ${stat}</div>`)
}

const processHtml = (task, destElem, detail, forceOpen, tag) => html => {
  destElem.html(html)
  openCloseMyItems(destElem)
  openCloseItems(destElem)
  activateFetch(destElem)
  activateActions(destElem)
  if (task != null) {
    flash(task)
  }
  let targetElem
  if (detail) {
    const child = destElem.children('details')
    child.unwrap()
    targetElem = child
  } else {
    targetElem = destElem
  }
  if (forceOpen) {
    let scrollElem
    if (tag) {
      const itemKey = targetElem.attr('itemkey')
      const jq = `[targetkey="${itemKey}"][tag="${tag}"]`
      scrollElem = $(jq)
    } else {
      scrollElem = targetElem
    }
    if (scrollElem && scrollElem[0]) {
      scrollElem[0].scrollIntoView(true)
    }
  }
}

const fetch = (url, task, destElem, data) => {
  if (data === undefined) {
    $.ajax({
      type: 'GET',
      url,
      processData: false,
      contentType: false,
      success: processHtml(task, destElem),
      error: report(task),
    })
  } else {
    $.ajax({
      type: 'POST',
      headers: { 'Content-Type': 'application/json' },
      url,
      data,
      processData: false,
      contentType: true,
      success: processHtml(task, destElem),
      error: report(task),
    })
  }
}

const fetchDetail = (url, task, destElem, forceOpen, tag) => {
  $.ajax({
    type: 'GET',
    url,
    processData: false,
    contentType: false,
    success: processHtml(task, destElem, true, forceOpen, tag),
    error: report(task),
  })
}

const report = task => (jqXHR, stat, error) => {
  if (task != null) {
    Console.error(stat, { error })
    flash(task, stat)
  }
}

const activateFetch = destElem => {
  const targets = destElem ? destElem.find('[fetchurl]') : $('[fetchurl]')
  targets.each((i, elem) => {
    const el = $(elem)
    const isFat = el.attr('fat')
    el.on('toggle', () => {
      const isOpen = elem.open
      if ((isOpen && isFat) || (!isOpen && !isFat)) {
        return
      }
      fetchDetailOpen(el)
    })
  })
}

const fetchDetailOpen = (el, tag) => {
  const forceOpen = el.attr('forceopen')
  const fetchUrl = el.attr('fetchurl') || emptyS
  const urlTitle = el.attr('urltitle') || emptyS
  const urlExtra = el.attr('urlextra') || emptyS
  const url = tag ? fetchUrl + urlExtra : fetchUrl + urlTitle + urlExtra
  el.wrap('<div></div>')
  const parent = el.closest('div')
  el.remove()
  fetchDetail(url, null, parent, forceOpen, tag)
}

const openCloseItems = destElem => {
  const targets = destElem ? destElem.find('details[itemkey]') : $('details[itemkey]')
  targets.each((i, elem) => {
    const el = $(elem)
    const itemKey = el.attr('itemkey')
    el.on('toggle', () => {
      if (elem.open) {
        localStorage.setItem(itemKey, 'open')
      } else {
        localStorage.setItem(itemKey, '')
      }
    })
    const forceOpen = el.attr('forceopen')
    const curOpen = el.prop('open')
    const prevOpen = localStorage.getItem(itemKey)
    const mustBeOpen = prevOpen || forceOpen
    if (curOpen) {
      if (!mustBeOpen) {
        el.prop('open', false)
      }
    } else if (!curOpen) {
      if (mustBeOpen) {
        el.prop('open', true)
      }
    }
  })
}

const openCloseMyItems = destElem => {
  const triggerPat = (itemKey, t) => `[itemkey="${itemKey}"][trigger="${t}"]`
  const targets = destElem ? destElem.find('[itemkey][body]') : $('[itemkey][body]')
  targets.each((i, elem) => {
    const body = $(elem)
    const itemKey = body.attr('itemkey')
    const triggerOn = destElem
      ? destElem.find(triggerPat(itemKey, '1'))
      : $(triggerPat(itemKey, '1'))
    const triggerOff = destElem
      ? destElem.find(triggerPat(itemKey, '-1'))
      : $(triggerPat(itemKey, '-1'))
    triggerOn.on('click', () => {
      localStorage.setItem(itemKey, 'open')
      body.show()
      triggerOn.hide()
      triggerOff.show()
    })
    triggerOff.on('click', () => {
      localStorage.setItem(itemKey, '')
      body.hide()
      triggerOn.show()
      triggerOff.hide()
    })
    const prevOpen = localStorage.getItem(itemKey)
    if (prevOpen) {
      body.show()
      triggerOn.hide()
      triggerOff.show()
    } else {
      body.hide()
      triggerOn.show()
      triggerOff.hide()
    }
  })
}

const Console = console

const makeFieldUrl = (table, eid, field, action) =>
  `/api/${table}/item/${eid}/field/${field}?action=${action}`

const collectEvents = {}

const view = (table, eid, field, valueEl, parent) => {
  const saveValue = save(table, eid, field, valueEl)
  const url = makeFieldUrl(table, eid, field, 'view')
  const task = saveValue === undefined ? null : `save ${field}`
  fetch(url, task, parent, saveValue)
}

const edit = (table, eid, field, valueEl, parent, newTag) => {
  const saveValue = save(table, eid, field, valueEl, newTag)
  const url = makeFieldUrl(table, eid, field, 'edit')
  const task = saveValue === undefined ? null : `save ${field}`
  fetch(url, task, parent, saveValue)
}

const refresh = el => {
  const targetKey = el.attr('targetkey')
  if (targetKey) {
    const targetElem = $(`[itemkey="${targetKey}"]`)
    targetElem.attr('fat', '')
    targetElem.attr('forceopen', '1')
    const tag = el.attr('tag')
    fetchDetailOpen(targetElem, tag)
  } else {
    const currentUrl = window.location.href
    window.location.href = currentUrl
  }
}

const getDynValues = (valueEl, newTag) => {
  const origAttValue = valueEl.attr('orig')
  if (origAttValue === undefined) {
    return emptyO
  }
  const origValue = atob(origAttValue)
  const multiple = valueEl.attr('multiple')
  const extensible = valueEl.attr('extensible')
  const valueCarrier = valueEl.find('.wvalue')
  const wType = valueEl.attr('wtype')
  const {
    [wType]: { read, readMultiple },
  } = widgets
  const givenValuePre = multiple
    ? readMultiple
      ? readMultiple(valueCarrier)
      : $.makeArray(valueCarrier.map((i, el) => read($(el)))).filter(v => v !== '')
    : read(valueCarrier)
  const givenValue =
    extensible && newTag
      ? multiple
        ? [...givenValuePre, [newTag]]
        : [newTag]
      : givenValuePre
  const newValue = JSON.stringify(givenValue)
  const dirty = origValue != newValue
  return { origValue, givenValue, newValue, dirty }
}

const save = (table, eid, field, valueEl, newTag) => {
  const { origValue, givenValue, newValue, dirty } = getDynValues(valueEl, newTag)
  if (origValue === undefined) {
    return undefined
  }

  if (DEBUG) {
    const wType = valueEl.attr('wtype')
    const dirtyRep = dirty ? 'dirty' : 'clean'
    const actionRep = dirty ? (SAVE ? 'saving' : 'suppress saving') : 'no save'
    Console.log(`WIDGET ${wType}: ${dirtyRep} => ${actionRep}`, {
      valueEl,
      origValue,
      newValue,
    })
  }
  return dirty && SAVE ? JSON.stringify({ save: givenValue }) : undefined
}

const activateActions = destElem => {
  const targets = destElem ? destElem.find('[action]') : $('[action]')
  targets.each((i, elem) => {
    const el = $(elem)
    const action = el.attr('action')

    if (action == 'refresh') {
      el.off('click').click(e => {
        e.preventDefault()
        e.stopPropagation()
        refresh(el)
      })
      return
    }

    const table = el.attr('table')
    const eid = el.attr('eid')
    const field = el.attr('field')
    const parent = $(elem.closest('div'))
    const valueEl = parent.find('[orig]')
    const focusEl = parent.find('input,textarea')

    if (action == 'edit') {
      parent.removeClass('edit')
    } else if (action == 'view') {
      parent.addClass('edit')
    }
    const actionFunc = action == 'edit' ? edit : view

    el.off('mousedown').mousedown(() => {
      const eventKey = `${table}:${eid}.${field}`
      collectEvents[eventKey] = true
    })
    el.off('click').click(() => {
      const eventKey = `${table}:${eid}.${field}`
      actionFunc(table, eid, field, valueEl, parent)
      collectEvents[eventKey] = false
    })
    focusEl.off('keyup').keyup(() => {
      const { dirty } = getDynValues(valueEl)
      if (dirty) {
        valueEl.addClass('dirty')
      } else {
        valueEl.removeClass('dirty')
      }
    })
    if (BLUR) {
      if (focusEl.length) {
        focusEl.off('blur').blur(() => {
          const eventKey = `${table}:${eid}.${field}`
          if (collectEvents[eventKey]) {
            collectEvents[eventKey] = false
          } else {
            edit(table, eid, field, valueEl, parent)
          }
        })
      }
    }
    const wType = valueEl.attr('wtype')
    const { [wType]: widget } = widgets
    if (widget) {
      const widgetTargets = valueEl.find('.wvalue')
      widget.activate(table, eid, field, parent, valueEl, widgetTargets)
    }
  })
}

const applyOptions = (destElem, optionElements, init) => {
  const options = {}
  optionElements.each((i, elem) => {
    const el = $(elem)
    const option = el.attr('id')
    const value = elOption(el)
    if (init) {
      elOption(el, value)
    }
    options[option] = value
  })
  const optionRep = Object.entries(options)
    .map(([op, v]) => `${op}=${v}`)
    .join('&')
  const links = destElem.find('a[hrefbase]')
  links.each((i, elem) => {
    const el = $(elem)
    const urlPrefix = el.attr('hrefbase')
    const urlSep = urlPrefix.indexOf('?') >= 0 ? '&' : '?'
    const url = `${urlPrefix}${optionRep ? urlSep : ''}${optionRep}`
    el.attr('href', url)
  })
  if (!init) {
    const activeLink = destElem.find('a.active')
    if (activeLink.length) {
      const activeUrl = activeLink.attr('href')
      window.location.href = activeUrl
    }
  }
}

const elOption = (el, value) => {
  if (value === undefined) {
    return el.attr('trival') || '0'
  } else {
    el.attr('trival', value || '0')
    if (value == '1') {
      el.prop('checked', true)
      el.prop('indeterminate', false)
    } else if (value == '-1') {
      el.prop('checked', false)
      el.prop('indeterminate', false)
    } else {
      el.prop('indeterminate', true)
    }
  }
}

const nextOption = val => (val == '1' ? '0' : val == '-1' ? '1' : '-1')

const activateOptions = destElem => {
  const optionElements = destElem.find('input.option')
  optionElements.each((i, elem) => {
    const el = $(elem)
    el.off('click').click(() => {
      const prevValue = elOption(el)
      const newValue = nextOption(prevValue)
      elOption(el, newValue)
      applyOptions(destElem, optionElements)
    })
  })
  applyOptions(destElem, optionElements, true)
}

const activateCfilter = () => {
  const cfilter = 'cfilter'
  const fcontrol = $('#cfilter')
  const clist = $('.table.contrib')
  const summaries = clist
    .children('details')
    .map((i, elem) => $(elem).children('summary'))

  const adjust = pat => {
    summaries.each((i, elem) => {
      const el = $(elem)
      const text = el.html().toLowerCase()
      if (text.indexOf(pat) == -1) {
        el.hide()
      } else {
        el.show()
      }
    })
  }
  const prevPat = localStorage.getItem(cfilter)
  if (prevPat) {
    fcontrol.val(prevPat)
    adjust(prevPat)
  }

  fcontrol.on('keyup', () => {
    const pat = fcontrol.val().toLowerCase()
    localStorage.setItem(cfilter, pat)
    adjust(pat)
  })
}

const xTouched = {}

const openGid = gid => {
  $(`tr[gid="${gid}"].dd`).show()
}

const closeGid = gid => {
  $(`tr[gid="${gid}"].dd`).hide()
}
const closeGidH = gid => {
  closeGid(gid)
  const children = groupRel[gid]
  if (children != null) {
    children.forEach(child => {
      closeGidH(child)
    })
  }
}
const openGidH = gid => {
  openGid(gid)
  const children = groupRel[gid]
  if (children != null) {
    children.forEach(child => {
      const touched = xTouched[child]
      if (touched) {
        openGidH(child)
      }
    })
  }
}

const setGid = (me, on, inv, method) => {
  const gid = me.attr('gid')
  const gKey = `group${gid}`
  const isDone = me.css('display') == 'none'
  if (!isDone) {
    const other = $(`a[gid="${gid}"].dc.i-${inv}`)
    me.hide()
    xTouched[gid] = on
    method(gid)
    other.show()
  }
    localStorage.setItem(gKey, on ? 'open' : '')
}

const initExpandControls = () => {
  $('.hide').hide()
  $('.dc.i-cdown').click(e => {
    e.preventDefault()
    const me = $(e.target)
    setGid(me, true, 'cup', openGidH)
  })
  $('.dc.i-cup').click(e => {
    e.preventDefault()
    const me = $(e.target)
    setGid(me, false, 'cdown', closeGidH)
  })
  $('.dca.i-addown').click(e => {
    e.preventDefault()
    const me = $(e.target)
    const gn = me.attr('gn')
    $(`.c-${gn} a.dc.i-cdown`).each((i, elem) => {
      const el = $(elem)
      setGid(el, true, 'cup', openGidH)
    })
  })
  $('.dca.i-adup').click(e => {
    e.preventDefault()
    const me = $(e.target)
    const gn = me.attr('gn')
    $(`.c-${gn} a.dc.i-cup`).each((i, elem) => {
      const el = $(elem)
      setGid(el, false, 'cdown', closeGidH)
    })
  })
  $('.dc.i-cdown').each((i, elem) => {
    const el = $(elem)
    const gid = el.attr('gid')
    const gKey = `group${gid}`
    const prevOpen = localStorage.getItem(gKey)
    if (prevOpen) {
      setGid(el, true, 'cup', openGidH)
    }
  })
}

/* main
 *
 */

$(() => {
  const sidebar = $('#sidebar')
  openCloseMyItems()
  openCloseItems()
  activateFetch()
  activateActions()
  activateOptions(sidebar)
  activateCfilter()
  initExpandControls()
})
